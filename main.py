import os
from amplpy import modules
from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from fastapi.responses import StreamingResponse
from auth import verify_token
from models.example.example_input import ExampleInput
from models.field_optimizer.field_optimizer_result import FieldOptimizerResult
from models.field_optimizer.field_optimizer_payload import FieldOptimizerPayload
from services.example_service import ExampleService
from services.field_optimizer_service import FieldOptimizerService


# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()


# Activate license when the app starts
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
    result = ExampleService.solve_a_b(payload)
    return result


@app.post("/solve-example")
async def solve_example(payload: ExampleInput, _: str = Depends(verify_token)):
    result = ExampleService.solve_example(payload)
    return result


@app.post("/solve-field-optimizer")
async def solve_field_optimizer(
    payload: FieldOptimizerPayload, _: str = Depends(verify_token)
) -> FieldOptimizerResult:
    result = FieldOptimizerService.solve(payload)
    return result


@app.post("/solve-field-optimizer-stream")
async def solve_field_optimizer_stream(
    payload: FieldOptimizerPayload, _: str = Depends(verify_token)
):
    return StreamingResponse(
        FieldOptimizerService.solve_stream(payload),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
