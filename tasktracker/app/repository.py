from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.future import select
from app.models import AuthIdentity, Account, Task, Status


class AuthIdentityRepository:
    def __init__(self, async_session: async_sessionmaker[AsyncSession]):
        self.async_session = async_session

    async def get_auth_identity_by_token(self, token: str) -> Optional[AuthIdentity]:
        async with self.async_session() as session:
            result = await session.execute(select(AuthIdentity).filter_by(token=token))
            return result.scalar()

    async def delete_auth_identity(self, auth_identity: AuthIdentity) -> AuthIdentity:
        async with self.async_session() as session:
            await session.delete(auth_identity)
            await session.commit()
            return auth_identity


class AccountRepository:
    def __init__(self, async_session: async_sessionmaker[AsyncSession]):
        self.async_session = async_session

    async def get_account_by_public_id(self, public_id: str) -> Optional[Account]:
        with self.async_session() as session:
            result = await session.execute(
                select(Account).filter_by(public_id=public_id)
            )
            return result.scalar()

    async def add_account(self, account: Account) -> Account:
        with self.async_session() as session:
            session.add(account)
            await session.commit()
            await session.refresh(account)
            return account

    async def get_accounts(self):
        with self.async_session() as session:
            result = await session.execute(select(Account))
            return result.scalars().all()

    async def get_worker_accounts(self):
        with self.async_session() as session:
            result = await session.execute(select(Account).filter_by(role="worker"))
            return result.scalars().all()


class TaskRepository:
    def __init__(self, async_session: async_sessionmaker[AsyncSession]):
        self.async_session = async_session

    async def create_task(self, task: Task):
        with self.async_session() as session:
            session.add(task)
            await session.commit()
            await session.refresh(task)
            return task

    async def get_incomplete_tasks(self):
        with self.async_session() as session:
            result = await session.execute(
                select(Task).filter_by(status=Status.ASSIGNED)
            )
            return result.scalars().all()

    async def update_tasks(self, tasks: list[Task]):
        with self.async_session() as session:
            session.bulk_save_objects(tasks)
            await session.commit()
            return tasks

    async def get_task_by_id(self, id: int) -> Optional[Task]:
        with self.async_session() as session:
            result = await session.execute(select(Task).filter_by(id=id))
            return result.scalar()

    async def update_task(self, task: Task) -> Task:
        with self.async_session() as session:
            session.add(task)
            await session.commit()
            await session.refresh(task)
            return task
