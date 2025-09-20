from pydantic import BaseModel


class FieldAllocation(BaseModel):
    field: str
    group: str
    timeslot: int
