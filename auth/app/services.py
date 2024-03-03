from typing import Optional
from app.security import verify_password
from app.models import Account
from app.crud import UserRepository


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def get_account_by_username(self, username: str) -> Optional[Account]:
        return await self.user_repo.get_account_by_username(username)

    async def get_account_by_public_id(self, public_id: str) -> Optional[Account]:
        return await self.user_repo.get_account_by_public_id(public_id)

    async def authenticate_account(
        self, username: str, password: str
    ) -> Optional[Account]:
        account = await self.user_repo.get_account_by_username(username)
        if account and verify_password(password, account.encrypted_password):
            return account
        return None

    async def create_account(self, account: Account) -> Account:
        return await self.user_repo.create_account(account)

    async def delete_account(self, account: Account) -> Account:
        return await self.user_repo.delete_account_by_public_id(account.public_id)

    async def update_account(self, account: Account) -> Account:
        return await self.user_repo.update_account(account)
