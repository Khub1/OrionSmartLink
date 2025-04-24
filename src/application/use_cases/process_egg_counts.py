from datetime import date
from typing import Optional
from src.domain.entities.egg_count import EggCount
from src.domain.interfaces.orion_repository import OrionDeviceRepository
from src.domain.interfaces.database_repository import DatabaseRepository

class ProcessEggCountsUseCase:
    def __init__(self, orion_repo: OrionDeviceRepository, db_repo: DatabaseRepository, fila_mapping: dict):
        self.orion_repo = orion_repo
        self.db_repo = db_repo
        self.fila_mapping = fila_mapping

    def execute(self, aviary_id: int, count_date: date) -> Optional[EggCount]:
        date_str = count_date.strftime("%Y-%m-%d")
        counts = self.orion_repo.fetch_egg_counts(aviary_id, date_str)
        if not counts:
            return None
        success = self.db_repo.upsert_egg_counts(aviary_id, count_date, counts, self.fila_mapping)
        if not success:
            return None
        return EggCount(aviary_id=aviary_id, date=count_date, counts=counts, fila_mapping=self.fila_mapping)
