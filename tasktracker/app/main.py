from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordBearer
import app.database as db
from app.repository import (
    AuthIdentityRepository,
    AccountRepository,
    TaskRepository,
)
from typing import Annotated
from app.models import Account
from app.services import TaskService, AuthService, AccountService
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import json
import os
import asyncio


app = FastAPI()
tokenUrl = os.environ.get("AUTH_SERVICE_URL") + "/token"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=tokenUrl)

authIdentityRepo = AuthIdentityRepository(db.AsyncSession)
accountRepo = AccountRepository(db.AsyncSession)
taskRepo = TaskRepository(db.AsyncSession)

tasksService = TaskService(taskRepo, accountRepo)
authService = AuthService(accountRepo, authIdentityRepo)
accountService = AccountService(accountRepo)

producer = AIOKafkaProducer(
    bootstrap_servers=os.environ.get("KAFKA_BOOTSTRAP_SERVERS"),
    value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
)

consumer = AIOKafkaConsumer(
    "account-stream",
    bootstrap_servers=os.environ.get("KAFKA_BOOTSTRAP_SERVERS"),
    group_id="tasktracker",
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    offset_reset="earliest",
)


async def get_current_account(token: Annotated[str, Depends(oauth2_scheme)]):
    return await authService.get_current_account(token)


async def consume():
    await consumer.start()
    try:
        async for message in consumer:
            event = message.value
            print(f"Received event: {event}")
            if event["event_type"] == "AccountCreatedEvent":
                accountService.on_account_created(event["payload"])
            elif event["event_type"] == "AccountDeletedEvent":
                accountService.on_account_deleted(event["payload"])
            elif event["event_type"] == "AccountUpdatedEvent":
                accountService.on_account_updated(event["payload"])
    finally:
        await consumer.stop()


@app.on_event("startup")
async def startup():
    await producer.start()
    asyncio.create_task(consume())


@app.on_event("shutdown")
async def shutdown():
    await producer.stop()


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
    # TODO: produce event TaskAssignedEvent(result)
    return {"message": "Task created successfully"}


@app.put("/shuffle")
async def shuffle_tasks(
    current_account: Annotated[Account, Depends(get_current_account)]
):
    result = await tasksService.shuffle_tasks(current_account)
    # TODO: produce event TaskAssignedEvent(result)
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
