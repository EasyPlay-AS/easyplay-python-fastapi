from pydantic import BaseModel
from .field_activity import FieldActivity


class FieldOptimizerResponse(BaseModel):
    result: str
    duration_ms: float
    preference_score: float
    activities: list[FieldActivity]
