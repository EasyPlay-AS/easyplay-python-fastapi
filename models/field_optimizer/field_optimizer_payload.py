from pydantic import BaseModel


class Stadium(BaseModel):
    id: str
    name: str
    size: int
    unavailable_start_times: list[int]


class TimeRange(BaseModel):
    start_time: str
    end_time: str
    day_indexes: list[int]


class Team(BaseModel):
    id: str
    name: str
    min_number_of_activities: int
    max_number_of_activities: int
    time_range: TimeRange
    duration: int
    size_required: int
    priority: int
    is_included: bool


class ExistingTeamActivity(BaseModel):
    team_id: str
    team_name: str
    stadium_id: str
    stadium_name: str
    start_timeslot: int
    end_timeslot: int
    duration_slots: int
    size_required: int


class FieldOptimizerPayload(BaseModel):
    stadiums: list[Stadium]
    teams: list[Team]
    existing_team_activities: list[ExistingTeamActivity]
    start_time: str
    end_time: str
    incompatible_groups: list[list[str]] | None = None
