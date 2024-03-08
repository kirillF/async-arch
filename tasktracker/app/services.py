from fastapi import HTTPException, status
from app.repository import TaskRepository, AccountRepository, AuthIdentityRepository
from app.models import Account, Task, Status, AuthIdentity
from datetime import datetime
import httpx
import random
import asyncio
import os
import httpx


class AuthService:
    verify_url = os.environ.get("AUTH_SERVICE_URL") + "/verify"

    def __init__(
        self, account_repo: AccountRepository, identity_repo: AuthIdentityRepository
    ):
        self.account_repo = account_repo
        self.identity_repo = identity_repo

    async def get_current_account(self, token: str):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            authIdentity = await self.identity_repo.get_auth_identity_by_token(token)
            if not authIdentity:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        self.verify_url,
                        headers={"Authorization": f"Bearer {token}"},
                    )
                    if response.status_code == 200:
                        account_id = response.json().get("account_id")
                        account = await self.account_repo.get_account_by_public_id(
                            account_id
                        )
                        if not account:
                            account = Account(
                                public_id=account_id,
                                role=response.json().get("role"),
                                username=response.json().get("username"),
                            )
                            account = await self.account_repo.add_account(account)
                            print(account)
                        authIdentity = await self.identity_repo.add_auth_identity(
                            AuthIdentity(
                                token=token,
                                account_id=account.id,
                                expires_at=datetime.fromtimestamp(
                                    response.json().get("expires_at")
                                ),
                            )
                        )
                        return account
                raise credentials_exception
            if authIdentity.expires_at < datetime.now():
                await self.identity_repo.delete_auth_identity(authIdentity)
                raise credentials_exception
            return await self.account_repo.get_account_by_id(authIdentity.account_id)
        except:
            raise credentials_exception


class TaskService:
    def __init__(self, task_repo: TaskRepository, account_repo: AccountRepository):
        self.task_repo = task_repo
        self.account_repo = account_repo

    async def get_tasks_for_account(self, account: Account):
        pass

    async def create_task(self, title: str, description: str, account: Account):
        task = Task(title=title, description=description)
        accounts = await self.account_repo.get_accounts()
        assignee = random.choice(accounts)
        task.assigned_to = assignee.id
        await self.task_repo.create_task(task)
        return task

    async def shuffle_tasks(self, account: Account):
        if account.role != "admin":
            raise Exception("Only admin can shuffle tasks")
        tasks = await self.task_repo.get_incomplete_tasks()
        accounts = await self.account_repo.get_worker_accounts()
        for task in tasks:
            assignee = random.choice(accounts)
            task.assigned_to = assignee.id
        await self.task_repo.update_tasks(tasks)
        return tasks

    async def complete_task(self, id: int, account: Account):
        task = await self.task_repo.get_task_by_id(id)
        if not task:
            raise Exception("Task not found")
        if task.assigned_to != account.id:
            raise Exception("Task is not assigned to you")
        task.status = Status.COMPLETED
        await self.task_repo.update_task(task)
        return task


class AccountService:
    def __init__(self, account_repo: AccountRepository):
        self.account_repo = account_repo

    async def on_account_created(self, event):
        account = Account(
            public_id=event["account_id"],
            username=event["username"],
            role=event["role"],
        )
        return await self.account_repo.add_account(account)

    async def on_account_deleted(self, event):
        account = await self.account_repo.get_account_by_public_id(event["account_id"])
        await self.account_repo.delete_account(account)

    async def on_account_updated(self, event):
        account = await self.account_repo.get_account_by_public_id(event["account_id"])
        account.username = event["username"]
        account.role = event["role"]
        await self.account_repo.update_account(account)

    async def get_account_by_public_id(self, public_id: str):
        return await self.account_repo.get_account_by_public_id(public_id)

    async def delete_account(self, account: Account):
        return await self.account_repo.delete_account(account)

    async def update_account(self, account: Account):
        return await self.account_repo.update_account(account)
