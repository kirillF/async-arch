from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordBearer


app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://localhost:3000/login")


@app.get("/")
async def index():
    return {"message": "Hello, World"}


@app.get("/tasks")
async def get_tasks(token: str = Depends(oauth2_scheme)):
    return {"tasks": []}


@app.get("/tasks/{id}")
async def get_task(id: int, token: str = Depends(oauth2_scheme)):
    return {"task": {"id": id, "description": "Task description"}}


@app.post("/tasks")
async def create_task(token: str = Depends(oauth2_scheme)):
    return {"message": "Task created successfully"}


@app.put("/tasks/{id}")
async def update_task(id: int, token: str = Depends(oauth2_scheme)):
    return {"message": f"Task {id} updated successfully"}


@app.put("/tasks/{id}/assign")
async def assign_task(id: int, token: str = Depends(oauth2_scheme)):
    return {"message": f"Task {id} assigned successfully"}


@app.put("/tasks/assign")
async def assign_tasks(token: str = Depends(oauth2_scheme)):
    return {"message": "Tasks assigned successfully"}
