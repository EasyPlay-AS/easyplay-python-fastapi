from datetime import datetime
from enum import Enum
from pydantic import BaseModel
from models.event import Event


class Result(str, Enum):
    SUCCESS = "success"
    ERROR = "error"


class OptimizationOutput(BaseModel):
    start_time: datetime
    duration_ms: float
    result: Result
    score: float
    events: list[Event]
