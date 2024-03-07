from fastapi import FastAPI, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
import app.database as db
from tasktracker.app.repository import (
    AuthIdentityRepository,
    AccountRepository,
    TaskRepository,
)
from datetime import datetime
from typing import Annotated
from app.models import Account
from app.services import TaskService


app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://auth:3000/token")

authIdentityRepo = AuthIdentityRepository(db.AsyncSession)
accountRepo = AccountRepository(db.AsyncSession)
taskRepo = TaskRepository(db.AsyncSession)

tasksService = TaskService(taskRepo, accountRepo)


async def get_current_account(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        authIdentity = await authIdentityRepo.get_auth_identity_by_token(token)
        if authIdentity is None:
            raise credentials_exception
        if authIdentity.expires_at < datetime.now():
            await authIdentityRepo.delete_auth_identity(authIdentity)
            raise credentials_exception
        return await accountRepo.get_account_by_id(authIdentity.account_id)
    except:
        raise credentials_exception


@app.get("/")
async def index(current_account: Annotated[Account, Depends(get_current_account)]):
    return {"message": "Hello, World"}


@app.post("/create_task")
async def create_task(
    title: str,
    description: str,
    current_account: Annotated[Account, Depends(get_current_account)],
):
    result = await tasksService.create_task(title, description, current_account)
    # TODO: produce event TaskCreatedEvent(result)
    return {"message": "Task created successfully"}


@app.put("/shuffle")
async def shuffle_tasks(
    current_account: Annotated[Account, Depends(get_current_account)]
):
    result = await tasksService.shuffle_tasks(current_account)
    # TODO: produce batch event TaskShuffledEvent(result)
    return {"message": "Tasks shuffled successfully"}


@app.put("/complete_task")
async def complete_task(
    id: int, current_account: Annotated[Account, Depends(get_current_account)]
):
    result = await tasksService.complete_task(id, current_account)
    # TODO: produce event TaskCompletedEvent(result)
    return {"message": "Task completed successfully"}


@app.get("/tasks")
async def get_tasks(token: Annotated[str, Depends(oauth2_scheme)]):
    return {"tasks": []}
