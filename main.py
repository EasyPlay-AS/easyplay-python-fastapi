from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from auth import verify_token
from utils.ampl_utils import activate_ampl_license
from models.example.example_input import ExampleInput
from models.field_optimizer.field_optimizer_input import FieldOptimizerInput
from services.example_service import ExampleService
from services.field_optimizer_service import FieldOptimizerService


# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()


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
    result = ExampleService.solve_a_b(payload)
    return result


@app.post("/solve-example")
async def solve_example(payload: ExampleInput, _: str = Depends(verify_token)):
    result = ExampleService.solve_example(payload)
    return result


@app.post("/solve-field-optimizer")
async def solve_field_optimizer(payload: FieldOptimizerInput, _: str = Depends(verify_token)):
    result = FieldOptimizerService.solve(payload)
    return result
