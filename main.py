
from datetime import datetime
from amplpy import AMPL, modules
from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from auth import verify_token
from models.example.example_input import ExampleInput
from models.example.example_output import ExampleOutput


# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()


# Activate AMPL license
# AMPL_LICENSE_UUID = "9644d103-8697-465c-8609-bf247c76e681"
# modules.activate(AMPL_LICENSE_UUID)


@app.get("/")
async def root():
    return {
        "message": (
            "Welcome to EasyPlay Python FastAPI! "
            "Swagger UI documentation is available at /docs"
        )
    }


@app.post("/solve-test")
async def solve_test():
    try:
        ampl = AMPL()
        ampl.option["solver"] = "scip"

        ampl.eval("""
            param a;
            param b;
            var x >= 0;
            maximize Objective: a * b * x;
            subject to limit: x <= b + 0.99;
        """)

        ampl.param["a"] = 10
        ampl.param["b"] = 5

        ampl.solve()

        solve_result = ampl.get_value("solve_result")
        if solve_result != "solved":
            return {
                "result": "FAILURE",
                "error": f"Solver failed with result: {solve_result}"
            }

        ampl_objective = ampl.obj["Objective"].value()
        ampl_x = ampl.var["x"].value()

        return {
            "objective": ampl_objective,
            "x": ampl_x
        }
    except Exception as e:
        return {"error": str(e)}


@app.post("/solve-a-b")
async def solve_a_b(payload: ExampleInput, _: str = Depends(verify_token)):
    start_time = datetime.now()

    try:
        # Initialize AMPL
        ampl = AMPL()

        # Load the model file
        ampl.read("ampl/a_b.mod")

        # Set the parameters from the payload
        ampl.param["a"] = payload.a
        ampl.param["b"] = payload.b

        # Solve the model
        ampl.solve()

        # Check solve status
        solve_result = ampl.get_value("solve_result")
        if solve_result != "solved":
            return {
                "result": "FAILURE", "error":
                f"Solver failed with result: {solve_result}"
            }

        # Extract results - CORRECTED METHOD
        objective = ampl.obj["Objective"]
        objective_value = objective.value()

        # Build the response
        end_time = datetime.now()
        duration_ms = round((end_time - start_time).total_seconds() * 1000, 2)

        output = ExampleOutput(
            result="SUCCESS",
            objective_value=objective_value,
            variable_values={},
            duration_ms=duration_ms,
        )
        return output
    except Exception as e:
        # Handle errors gracefully
        return {"result": "FAILURE", "error": str(e)}


@app.post("/solve-example")
async def solve_example(payload: ExampleInput, _: str = Depends(verify_token)):
    start_time = datetime.now()

    try:
        # Initialize AMPL
        ampl = AMPL()

        # Specify the solver
        # ampl.option["solver"] = "scip"

        # Load the model file
        ampl.read("ampl/example.mod")

        # Set the parameters from the payload
        ampl.param["a"] = payload.a
        ampl.param["b"] = payload.b

        # Solve the model
        ampl.solve()

        # Check solve result
        solve_result = ampl.get_value("solve_result")
        if solve_result != "solved":
            return {
                "result": "FAILURE",
                "error": f"Solver failed with result: {solve_result}"
            }

        # Extract results
        objective = ampl.obj["Objective"]
        objective_value = objective.value()

        # Get variables - Iterate over the EntityMap to get all variable values
        variable_values = {
            "x": ampl.get_variable("x").value(),
        }

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
