import logging
from zoneinfo import ZoneInfo
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import date, datetime
from concurrent.futures import ThreadPoolExecutor
from typing import List
from src.application.use_cases.process_egg_counts import ProcessEggCountsUseCase
from src.config.settings import AVIARY_CONFIGS
from src.infrastructure.orion.client import OrionClient
from src.infrastructure.database.sql_server_repository import SqlServerRepository
import asyncio
import traceback

logger = logging.getLogger(__name__)

class EggCountScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone=ZoneInfo('America/Argentina/Buenos_Aires'))
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.working_aviaries = [15, 16, 17, 18, 19, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 38]
        missing = [avid for avid in self.working_aviaries if avid not in AVIARY_CONFIGS]
        if missing:
            logger.error(f"Missing configs for aviaries: {missing}")

    def process_aviary(self, aviary_id: int, date: date) -> bool:
        try:
            config = AVIARY_CONFIGS[aviary_id]
            orion_client = OrionClient(
                ip=config.ip,
                port=config.port,
                devcmd=config.devcmd,
                num_rows=config.num_rows,
                target_cmd=config.target_cmd,
                response_size=config.response_size
            )
            db_repo = SqlServerRepository()
            use_case = ProcessEggCountsUseCase(
                orion_repo=orion_client,
                db_repo=db_repo,
                fila_mapping=config.fila_mapping
            )
            logger.debug(f"Executing for aviary {aviary_id} with date: {date} (type: {type(date)})")
            result = use_case.execute(aviary_id, date)
            if result:
                logger.info(f"Aviary {aviary_id} ({config.name}) processed: {len(result.counts)} counts")
                return True
            logger.error(f"Aviary {aviary_id} ({config.name}) failed to process")
            return False
        except Exception as e:
            logger.error(f"Aviary {aviary_id} ({config.name}) error: {str(e)}\n{traceback.format_exc()}")
            return False

    async def run_egg_counts_job(self):
        argentina_tz = ZoneInfo('America/Argentina/Buenos_Aires')
        now_argentina = datetime.now(argentina_tz)
        date_only = now_argentina.date()
        
        logger.info(f"Processing egg counts for {date_only} (Argentina time) at {now_argentina}")
        logger.debug(f"Full datetime in Argentina: {now_argentina.strftime('%Y-%m-%d %H:%M:%S %Z%z')}")

        logger.info(f"Starting egg count job for {len(self.working_aviaries)} aviaries: {self.working_aviaries}")
        
        failed_aviaries = []
        futures = [
            asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda avid=avid: (avid, self.process_aviary(avid, date_only))
            )
            for avid in self.working_aviaries
        ]
        results = await asyncio.gather(*futures, return_exceptions=True)
        
        successes = 0
        for aviary_id, result in results:
            if result is True:
                successes += 1
            else:
                failed_aviaries.append(aviary_id)
                logger.warning(f"Aviary {aviary_id} ({AVIARY_CONFIGS[aviary_id].name}) added to retry list")
        
        logger.info(f"Initial run completed: {successes}/{len(self.working_aviaries)} aviaries successful")
        
        total_successes = successes
        for attempt in range(1, 3):
            if not failed_aviaries:
                logger.info(f"No retries needed for attempt {attempt}; all aviaries processed")
                break
            
            logger.info(f"Retry attempt {attempt} for {len(failed_aviaries)} failed aviaries: {failed_aviaries}")
            retry_futures = [
                asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    lambda avid=avid: (avid, self.process_aviary(avid, date_only))
                )
                for avid in failed_aviaries
            ]
            retry_results = await asyncio.gather(*retry_futures, return_exceptions=True)
            
            retry_successes = 0
            still_failed = []
            for aviary_id, result in retry_results:
                if result is True:
                    retry_successes += 1
                    total_successes += 1
                else:
                    still_failed.append(aviary_id)
                    logger.error(f"Aviary {aviary_id} ({AVIARY_CONFIGS[aviary_id].name}) failed on retry attempt {attempt}")
            
            logger.info(f"Retry attempt {attempt} completed: {retry_successes}/{len(failed_aviaries)} aviaries successful")
            failed_aviaries = still_failed
        
        logger.info(f"Job summary: {total_successes}/{len(self.working_aviaries)} aviaries successful")
        if failed_aviaries:
            logger.error(f"Persistent failures after retries: {failed_aviaries}")

    def start(self):
        argentina_tz = ZoneInfo('America/Argentina/Buenos_Aires')
        utc_tz = ZoneInfo('UTC')
        now_utc = datetime.now(utc_tz)
        now_argentina = datetime.now(argentina_tz)
        
        logger.info(f"UTC Time: {now_utc.strftime('%Y-%m-%d %H:%M:%S %Z%z')}")
        logger.info(f"Argentina Time: {now_argentina.strftime('%Y-%m-%d %H:%M:%S %Z%z')}")
        logger.info(f"Scheduled jobs will run at these Argentina times: 3:59, 7:59, 11:59, 15:59, 19:59, 23:59")

        self.scheduler.add_job(
            self.run_egg_counts_job,
            'cron',
            hour='3,7,11,15,19,23',
            minute=59,
            second=0,
            timezone=ZoneInfo('America/Argentina/Buenos_Aires'),
            id='egg_counts_job',
            replace_existing=True
        )
        self.scheduler.start()
        logger.info("Cron schedule: 3:59, 7:59, 11:59, 15:59, 19:59, 23:59 Argentina time")

    def shutdown(self):
        self.scheduler.shutdown()
        self.executor.shutdown(wait=True)
        logger.info("Scheduler stopped")