import logging
from logging.handlers import TimedRotatingFileHandler
from zoneinfo import ZoneInfo
from datetime import datetime

class ArgentinaFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)
        self.tz = ZoneInfo('America/Argentina/Buenos_Aires')

    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, self.tz)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.strftime('%Y-%m-%d %H:%M:%S')

def setup_logging():
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    # File handler for persistent logs
    file_handler = TimedRotatingFileHandler('./src/logs/egg_counts.log', when='midnight', backupCount=7)
    file_handler.setFormatter(ArgentinaFormatter(
        fmt='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    logger.addHandler(file_handler)

    # Console handler for Docker logs
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ArgentinaFormatter(
        fmt='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    logger.addHandler(console_handler)