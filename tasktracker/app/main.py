from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
import app.database as db
from app.repository import (
    AuthIdentityRepository,
    AccountRepository,
    TaskRepository,
)
from typing import Annotated
from app.models import Account, Task
from app.services import TaskService, AuthService, AccountService
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import json
import os
import asyncio
import uuid
from pydantic import BaseModel
import logging


app = FastAPI()
tokenUrl = os.environ.get("AUTH_SERVICE_URL") + "/token"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=tokenUrl)

authIdentityRepo = AuthIdentityRepository(db.AsyncSession)
accountRepo = AccountRepository(db.AsyncSession)
taskRepo = TaskRepository(db.AsyncSession)

tasksService = TaskService(taskRepo, accountRepo)
authService = AuthService(accountRepo, authIdentityRepo)
accountService = AccountService(accountRepo)

task_stream_topic = "task-stream"
tasks_topic = "tasks"

producer = AIOKafkaProducer(
    bootstrap_servers=os.environ.get("KAFKA_BOOTSTRAP_SERVERS"),
    value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
)

consumer = AIOKafkaConsumer(
    "account-stream",
    bootstrap_servers=os.environ.get("KAFKA_BOOTSTRAP_SERVERS"),
    group_id="tasktracker",
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
)


async def get_current_account(token: Annotated[str, Depends(oauth2_scheme)]):
    return await authService.get_current_account(token)


async def consume():
    async for message in consumer:
        event = message.value
        logging.info(f"Received event: {event}")
        if event["event_type"] == "account_created":
            await accountService.on_account_created(event["payload"])
        elif event["event_type"] == "account_deleted":
            await accountService.on_account_deleted(event["payload"])
        elif event["event_type"] == "account_updated":
            await accountService.on_account_updated(event["payload"])


def create_task_event(event_type: str, task: Task):
    return {
        "event_type": event_type,
        "event_id": uuid.uuid4(),
        "payload": {
            "task_id": task.public_id,
            "assigned_to": task.assigned_to,
            "description": task.description,
        },
    }


class TaskReq(BaseModel):
    title: str
    description: str


@app.on_event("startup")
async def startup():
    await producer.start()
    await consumer.start()
    asyncio.create_task(consume())


@app.on_event("shutdown")
async def shutdown():
    await producer.stop()
    await consumer.stop()


@app.get("/")
async def index(current_account: Annotated[Account, Depends(get_current_account)]):
    tasks = await tasksService.get_tasks_for_account(current_account)
    return {"message": "Hello, World"}


@app.post("/create_task")
async def create_task(
    task: TaskReq,
    current_account: Annotated[Account, Depends(get_current_account)],
):
    result = await tasksService.create_task(
        task.title, task.description, current_account
    )
    producer.send_and_wait(
        task_stream_topic, value=create_task_event("task_created", result)
    )
    producer.send_and_wait(
        tasks_topic, value=create_task_event("task_assigned", result)
    )
    return {"message": "Task created successfully"}


@app.put("/shuffle")
async def shuffle_tasks(
    current_account: Annotated[Account, Depends(get_current_account)]
):
    try:
        result = await tasksService.shuffle_tasks(current_account)
        for task in result:
            producer.send_and_wait(
                tasks_topic, value=create_task_event("task_assigned", task)
            )
        return {"message": "Tasks shuffled successfully"}
    except:
        return HTTPException(status_code=400, detail="Only admin can shuffle tasks")


@app.put("/complete_task")
async def complete_task(
    id: int, current_account: Annotated[Account, Depends(get_current_account)]
):
    result = await tasksService.complete_task(id, current_account)
    producer.send_and_wait(
        tasks_topic, value=create_task_event("task_completed", result)
    )
    return {"message": "Task completed successfully"}


@app.get("/tasks")
async def get_tasks(token: Annotated[str, Depends(oauth2_scheme)]):
    return {"tasks": []}
