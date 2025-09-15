from pydantic import BaseModel


class ExampleOutput(BaseModel):
    result: str  # Whether the optimization succeeded
    objective_value: float  # Final value of the objective
    variable_values: dict  # Optimized variable values
    duration_ms: float  # Total computation time
