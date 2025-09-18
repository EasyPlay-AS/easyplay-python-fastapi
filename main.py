
import os
from datetime import datetime
from amplpy import AMPL, modules
from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from auth import verify_token
from models.example.example_input import ExampleInput
from models.example.example_output import ExampleOutput
from models.field_optimizer.field_optimizer_input import FieldOptimizerInput


# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()


def activate_ampl_license():
    """Activate AMPL license using environment variable"""
    license_uuid = os.getenv("AMPL_LICENSE_UUID")
    if license_uuid:
        try:
            modules.activate(license_uuid)
            print(f"AMPL license activated successfully: {license_uuid}")
        except Exception as e:
            print(f"Failed to activate AMPL license: {e}")
    else:
        print("No AMPL_LICENSE_UUID found in environment variables")


# Activate license when the app starts
activate_ampl_license()


@app.get("/")
async def root():
    return {
        "message": (
            "Welcome to EasyPlay Python FastAPI! "
            "Swagger UI documentation is available at /docs"
        )
    }


@app.post("/solve-a-b")
async def solve_a_b(payload: ExampleInput, _: str = Depends(verify_token)):
    start_time = datetime.now()

    try:
        # Initialize AMPL (no need to specify solver)
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
                "result": "FAILURE",
                "error": "Solver failed to solve the model"
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
        return {
            "result": "FAILURE",
            "error": str(e)
        }


@app.post("/solve-example")
async def solve_example(payload: ExampleInput, _: str = Depends(verify_token)):
    start_time = datetime.now()

    try:
        # Initialize AMPL with SCIP solver
        ampl = AMPL()
        ampl.option["solver"] = "scip"

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
                "error": "Solver failed to solve the model"
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
        return {
            "result": "FAILURE",
            "error": str(e)
        }


@app.post("/solve-field-optimizer")
async def solve_field_optimizer(payload: FieldOptimizerInput, _: str = Depends(verify_token)):

    print("PAYLOAD", payload)

    start_time = datetime.now()

    try:
        # Initialize AMPL with SCIP solver
        ampl = AMPL()

        ampl.option["solver"] = "scip"

        # Load the model file
        ampl.read("ampl/field_optimizer.mod")

        # ------
        # Set data from JSON payload instead of reading .dat file
        # ------

        # Set basic sets
        ampl.set["F"] = [field.name for field in payload.fields]
        ampl.set["G"] = [group.name for group in payload.groups]
        ampl.set["T"] = payload.time_slots

        # Set available starting times for each group (AT)
        for group in payload.groups:
            ampl.set["AT"][group.name] = group.possible_start_times

        # Set preferred starting times for each group (PT)
        for group in payload.groups:
            ampl.set["PT"][group.name] = group.preferred_start_times

        # Set unavailable times for each field (UT)
        for field in payload.fields:
            ampl.set["UT"][field.name] = field.unavailable_start_times

        # Set group parameters
        for group in payload.groups:
            ampl.param["d"][group.name] = group.duration
            ampl.param["n_min"][group.name] = group.minimum_number_of_activities
            ampl.param["n_max"][group.name] = group.maximum_number_of_activities
            ampl.param["size_req"][group.name] = group.size_required
            ampl.param["prio"][group.name] = group.priority
            ampl.param["p_st1"][group.name] = group.preferred_start_time_activity_1
            ampl.param["p_st2"][group.name] = group.preferred_start_time_activity_2

        # Set field parameters
        for field in payload.fields:
            ampl.param["size"][field.name] = field.size

        # Solve the model
        ampl.solve()

        # Check solve result
        solve_result = ampl.get_value("solve_result")
        if solve_result != "solved":
            return {
                "result": "FAILURE",
                "error": "Solver failed to solve the model"
            }

        preference_score = ampl.obj["preference_score"]
        preference_score_value = preference_score.value()

        # Build the response
        end_time = datetime.now()
        duration_ms = round((end_time - start_time).total_seconds() * 1000, 2)

        return {
            "result": "SUCCESS",
            "preference_score": preference_score_value,
            "duration_ms": duration_ms
        }
    except Exception as e:
        # Handle errors gracefully
        return {
            "result": "FAILURE",
            "error": str(e)
        }
