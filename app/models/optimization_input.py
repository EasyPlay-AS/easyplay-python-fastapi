from pydantic import BaseModel
from models.baneplan import Baneplan
from models.stadium import Stadium
from models.team import Team


class OptimizationInput(BaseModel):
    baneplan: Baneplan
    stadiums: list[Stadium]
    teams: list[Team]
