from fastapi import FastAPI
from fastapi import Request

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Welcome to EasyPlay Python FastAPI! Swagger UI documentation is available at /docs"}


@app.post("/optimization")
async def optimization(request: Request):
    data = await request.json()
    return {"message": "Optimization endpoint", "data": data}
