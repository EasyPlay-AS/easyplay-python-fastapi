from pydantic import BaseModel


class FieldActivity(BaseModel):
    field: str
    group: str
    start_timeslot: int
    end_timeslot: int
    duration: int
