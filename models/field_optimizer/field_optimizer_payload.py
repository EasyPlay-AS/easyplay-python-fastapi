from pydantic import BaseModel


class Stadium(BaseModel):
    id: str
    name: str
    size: int
    unavailable_start_times: list[int]


class Team(BaseModel):
    id: str
    name: str
    min_number_of_activities: int
    max_number_of_activities: int
    duration: int
    size_required: int
    priority: int
    is_included: bool


class FieldOptimizerPayload(BaseModel):
    stadiums: list[Stadium]
    teams: list[Team]
    start_time: str
    end_time: str
    incompatible_groups: list[list[str]] | None = None 
