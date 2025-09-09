from pydantic import BaseModel


class Baneplan(BaseModel):
    id: str
    name: str
