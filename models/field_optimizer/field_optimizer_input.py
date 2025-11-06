from pydantic import BaseModel


class Field(BaseModel):
    name: str
    size: int
    unavailable_start_times: list[int]


class Group(BaseModel):
    name: str
    minimum_number_of_activities: int
    maximum_number_of_activities: int
    possible_start_times: list[int]
    preferred_start_times: list[int]
    preferred_start_time_activity_1: int
    preferred_start_time_activity_2: int
    size_required: int
    duration: int
    priority: int
    preferred_field_names: list[str]


class FieldOptimizerInput(BaseModel):
    fields: list[Field]
    groups: list[Group]
    time_slots: list[list[int]]
