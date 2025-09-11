from pydantic import BaseModel


class ExampleInput(BaseModel):
    a: float  # Coefficient for the objective
    b: float  # Upper bound for the variable x
