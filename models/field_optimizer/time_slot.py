from pydantic import BaseModel


class TimeSlot(BaseModel):
    id: int
    time: str
    duration_minutes: int
    week_day_index: int
