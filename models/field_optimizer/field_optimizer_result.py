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


class IterationDetail(BaseModel):
    iteration: int
    time_limit: int
    gap_limit: float
    elapsed_ms: float
    solve_result: str
    preference_score: float | None
    gap_percent: float | None
    abs_gap: float | None


class FieldOptimizerResult(BaseModel):
    result: Literal["solved", "infeasible", "no_objective_value", "failure"]
    duration_ms: float
    preference_score: float | None
    activities: list[Activity]
    activities_not_generated: list[ActivitiesNotGenerated] | None = None
    error_message: str | None = None
    iterations: list[IterationDetail] | None = None
