from pydantic import BaseModel
from app.models import Role


class AccountBase(BaseModel):
    username: str


class CreateAccount(AccountBase):
    password: str


class Account(AccountBase):
    id: int
    role: Role

    class Config:
        orm_mode = True
