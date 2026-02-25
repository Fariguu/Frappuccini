from fastapi import FastAPI

app = FastAPI()

@app.get("/api")
async def root():
    return {"message": "Hello from FastAPI"}

@app.get("/api/hello")
async def hello():
    return {"message": "Hello from the backend!"}
