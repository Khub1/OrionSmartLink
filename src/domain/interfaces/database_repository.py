from abc import ABC, abstractmethod
from datetime import date
from typing import List

class DatabaseRepository(ABC):
    @abstractmethod
    def upsert_egg_counts(self, aviary_id: int, count_date: date, counts: List[int], fila_mapping: dict) -> bool:
        pass
