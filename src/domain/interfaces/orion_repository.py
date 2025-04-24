from abc import ABC, abstractmethod
from typing import List, Optional

class OrionDeviceRepository(ABC):
    @abstractmethod
    def fetch_egg_counts(self, aviary_id: int, date: str) -> Optional[List[int]]:
        pass
