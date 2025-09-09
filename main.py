
from datetime import datetime
import time
from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from auth import verify_token
from models.optimization_input import OptimizationInput
from models.optimization_output import OptimizationOutput, Result

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


@app.post("/optimization")
async def optimization(payload: OptimizationInput, _: str = Depends(verify_token)):
    start_time = datetime.now()

    # TODO: Remove mock sleep
    time.sleep(1)

    end_time = datetime.now()

    duration = end_time - start_time
    duration_ms = round(duration.total_seconds() * 1000, 2)

    # TODO: Calculate output
    optimization_output = OptimizationOutput(
        result=Result.SUCCESS,
        start_time=start_time,
        duration_ms=duration_ms,
        score=100.0,
        events=[]
    )

    return {
        "message": "Optimization endpoint",
        "output": optimization_output,
    }
