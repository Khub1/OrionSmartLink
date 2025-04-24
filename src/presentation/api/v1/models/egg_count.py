from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

class EggCountRequest(BaseModel):
    aviary_id: int
    date: str

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: str) -> str:
        try:
            input_date = datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")

        # Get current date in Asunción timezone (PYT, UTC-3 in April 2025)
        today = datetime.now(ZoneInfo("America/Asuncion")).date()
        # Define valid dates: today, yesterday, day before yesterday
        valid_dates = {today, today - timedelta(days=1), today - timedelta(days=2)}

        if input_date not in valid_dates:
            raise ValueError("La fecha debe ser la de hoy,ayer o anteayer")
        return value

class EggCountResponse(BaseModel):
    status: str
    message: str
    data: Optional[dict] = None  

