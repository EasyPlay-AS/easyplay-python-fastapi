from pydantic import BaseModel


class Team(BaseModel):
    id: str
    name: str
