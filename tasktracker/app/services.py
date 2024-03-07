from tasktracker.app.repository import TaskRepository, AccountRepository
from app.models import Account, Task, Status
import random


class TaskService:
    def __init__(self, task_repo: TaskRepository, account_repo: AccountRepository):
        self.task_repo = task_repo
        self.account_repo = account_repo

    async def create_task(self, title: str, description: str, account: Account):
        task = Task(title=title, description=description)
        accounts = await self.account_repo.get_accounts()
        assignee = random.choice(accounts)
        task.account_id = assignee.id
        await self.task_repo.create_task(task)
        return task

    async def shuffle_tasks(self, account: Account):
        tasks = await self.task_repo.get_incomplete_tasks()
        accounts = await self.account_repo.get_worker_accounts()
        for task in tasks:
            assignee = random.choice(accounts)
            task.account_id = assignee.id
        await self.task_repo.update_tasks(tasks)
        return tasks

    async def complete_task(self, id: int, account: Account):
        task = await self.task_repo.get_task_by_id(id)
        if not task:
            raise Exception("Task not found")
        if task.account_id != account.id:
            raise Exception("Task is not assigned to you")
        task.status = Status.COMPLETED
        await self.task_repo.update_task(task)
        return task
