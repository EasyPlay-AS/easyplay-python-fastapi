from pydantic import BaseModel


class Stadium(BaseModel):
    id: str
    name: str


class Team(BaseModel):
    id: str
    name: str


class Activity(BaseModel):
    stadium: Stadium
    team: Team
    index_week_day: int
    start_time: str
    end_time: str
    size: int


class FieldOptimizerResult(BaseModel):
    result: str
    duration_ms: float
    preference_score: float
    activities: list[Activity]
