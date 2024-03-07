from typing import Optional
from app.models import Account
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


class UserRepository:
    def __init__(self, async_session: async_sessionmaker[AsyncSession]):
        self.async_session = async_session

    async def get_account_by_username(self, username: str) -> Optional[Account]:
        async with self.async_session() as session:
            result = await session.execute(select(Account).filter_by(username=username))
            return result.scalar()

    async def get_account_by_public_id(self, public_id: str) -> Optional[Account]:
        async with self.async_session() as session:
            result = await session.execute(
                select(Account).filter_by(public_id=public_id)
            )
            return result.scalar()

    async def create_account(self, account: Account) -> Account:
        async with self.async_session() as session:
            session.add(account)
            await session.commit()
            await session.refresh(account)
            return account

    async def delete_account_by_public_id(self, public_id: str) -> Account:
        async with self.async_session() as session:
            result = await session.execute(
                select(Account).filter_by(public_id=public_id)
            )
            account = result.scalar()
            await session.delete(account)
            await session.commit()
            return account

    async def delete_account(self, account: Account) -> Account:
        async with self.async_session() as session:
            await session.delete(account)
            await session.commit()
            return account

    async def update_account(self, account: Account) -> Account:
        async with self.async_session() as session:
            session.add(account)
            await session.commit()
            await session.refresh(account)
            return account
