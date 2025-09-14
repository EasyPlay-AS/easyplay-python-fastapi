import subprocess
from datetime import datetime
from amplpy import AMPL
from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from auth import verify_token

from models.example.example_input import ExampleInput
from models.example.example_output import ExampleOutput


# Load environment variables
load_dotenv()


def activate_ampl_license():
    """Activate AMPL license using amplpy.modules activate command"""
    license_uuid = "9644d103-8697-465c-8609-bf247c76e681"

    try:
        # Try to activate with the license UUID
        result = subprocess.run(
            ["python", "-m", "amplpy.modules", "activate", license_uuid],
            capture_output=True,
            text=True,
            check=True
        )
        print(
            f"AMPL license activated successfully with UUID {license_uuid}: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to activate AMPL license: {e.stderr}")
        return False
    except Exception as e:
        print(f"Unexpected error activating AMPL license: {e}")
        return False


# Initialize FastAPI app
app = FastAPI()

# Activate license on startup
print("Activating AMPL license...")
LICENSE_ACTIVATED = activate_ampl_license()
if not LICENSE_ACTIVATED:
    print("Warning: AMPL license activation failed. Some features may not work properly.")


@app.post("/solve-example")
async def solve_example(payload: ExampleInput, _: str = Depends(verify_token)):
    start_time = datetime.now()

    try:
        # Initialize AMPL session
        ampl = AMPL()
        print("AMPL initialized", ampl)

        # Specify the solver
        ampl.setOption("solver", "scip")
        print("Solver set to scip")

        # Load the model file
        ampl.read("ampl/example.mod")
        print("Model file loaded")

        # Set the parameters from the payload
        ampl.param["a"] = payload.a
        ampl.param["b"] = payload.b
        print(f"Parameters set: a={payload.a}, b={payload.b}")

        # Solve the model
        print("Starting to solve...")
        ampl.solve()
        print("Solve completed")

        # Check solve status
        solve_status = ampl.getValue("solve_result")
        print(f"Solve status: {solve_status}")

        # Extract results - CORRECTED METHOD
        objective_value = ampl.obj["Objective"].value()
        print(f"Objective value: {objective_value}")

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
