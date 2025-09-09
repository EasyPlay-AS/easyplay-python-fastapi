from pydantic import BaseModel


class Stadium(BaseModel):
    id: str
    name: str
    number_of_zones: int
