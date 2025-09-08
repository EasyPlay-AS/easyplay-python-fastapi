from fastapi import FastAPI
from fastapi import Request

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Welcome to EasyPlay Python FastAPI"}


@app.post("/optimization")
async def optimization(request: Request):
    data = await request.json()
    return {"message": "Optimization endpoint", "data": data}
