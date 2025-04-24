from dataclasses import dataclass
from datetime import date
from typing import List

@dataclass
class EggCount:
    aviary_id: int
    date: date
    counts: List[int]
    fila_mapping: dict
