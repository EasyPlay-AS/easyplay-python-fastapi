from pydantic import BaseModel


class Event(BaseModel):
    id: str
    baneplan_id: str
    end_time: str
    stadium_id: str
    start_time: str
    team_id: str
    title: str
    weekday_index: int
