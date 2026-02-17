from typing import Literal
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


class ActivitiesNotGenerated(BaseModel):
    team: Team
    activities: int
    missing_activities: float


class FieldOptimizerResult(BaseModel):
    result: Literal["solved", "infeasible", "no_objective_value", "failure"]
    duration_ms: float
    preference_score: float | None
    activities: list[Activity]
    activities_not_generated: list[ActivitiesNotGenerated] | None = None
