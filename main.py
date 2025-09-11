from datetime import datetime
from amplpy import AMPL
from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from auth import verify_token

from models.example.example_input import ExampleInput
from models.example.example_output import ExampleOutput


load_dotenv()

app = FastAPI()


@app.get("/")
async def root():
    return {
        "message": (
            "Welcome to EasyPlay Python FastAPI! "
            "Swagger UI documentation is available at /docs"
        )
    }


@app.post("/solve-example")
async def solve_example(payload: ExampleInput, _: str = Depends(verify_token)):
    start_time = datetime.now()

    try:
        # Initialize AMPL session
        ampl = AMPL()

        # Specify the solver
        ampl.setOption("solver", "scip")

        # Load the model file
        ampl.read("ampl/example.mod")

        # Set the parameters from the payload
        ampl.param["a"] = payload.a
        ampl.param["b"] = payload.b

        # Solve the model
        ampl.solve()

        # Extract results - CORRECTED METHOD
        objective_value = ampl.obj["Objective"].value()
        print("RESULT objective_value", objective_value)

        # Get variables - Iterate over the EntityMap to get all variable values
        variable_values = {}
        variables = ampl.get_variables()

        for var_name, var_obj in variables:
            variable_values[var_name] = var_obj.value()
            print(f"Variable {var_name}: {var_obj.value()}")

        # Build the response
        end_time = datetime.now()
        duration_ms = round((end_time - start_time).total_seconds() * 1000, 2)

        output = ExampleOutput(
            result="SUCCESS",
            objective_value=objective_value,
            variable_values=variable_values,
            duration_ms=duration_ms,
        )
        return output

    except Exception as e:
        # Handle errors gracefully
        return {"result": "FAILURE", "error": str(e)}
