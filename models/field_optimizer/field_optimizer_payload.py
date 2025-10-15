from pydantic import BaseModel


class Stadium(BaseModel):
    id: str
    name: str
    size: int
    unavailableStartTimes: list[int]


class Team(BaseModel):
    id: str
    name: str
    minNumberOfActivities: int
    maxNumberOfActivities: int
    duration: int
    sizeRequired: int
    priority: int
    isIncluded: bool


class FieldOptimizerPayload(BaseModel):
    stadiums: list[Stadium]
    teams: list[Team]
    startTime: str
    endTime: str
