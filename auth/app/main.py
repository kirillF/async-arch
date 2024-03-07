from typing import Annotated
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.services import AuthService
from app.security import create_access_token, hash_password, decode_access_token
from app.models import Account
from app.repository import UserRepository
import jwt
import app.database as db
from aiokafka import AIOKafkaProducer
import os
import uuid
import json

# Create the FastAPI app
app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

user_repo = UserRepository(db.AsyncSession)
auth_service = AuthService(user_repo)

producer = AIOKafkaProducer(bootstrap_servers=os.environ.get("KAFKA_BOOTSTRAP_SERVERS"))


@app.on_event("startup")
async def startup():
    await producer.start()


@app.on_event("shutdown")
async def shutdown():
    await producer.stop()


topic = "account-stream"


def create_account_stream_event(event_type: str, account: Account):
    return json.dumps(
        {
            "event_type": event_type,
            "event_id": uuid.uuid4(),
            "payload": {
                "account_id": account.public_id,
                "username": account.username,
                "role": account.role,
            },
        },
    default=str).encode()


@app.post("/signup")
async def signup(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    existing_account = await auth_service.get_account_by_username(form_data.username)
    if existing_account:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = hash_password(form_data.password)
    account = Account(username=form_data.username, encrypted_password=hashed_password)
    account = await auth_service.create_account(account)

    await producer.send_and_wait(
        topic, value=create_account_stream_event("account_created", account)
    )
    return {"account_id": account.public_id, "status": "Account created"}


@app.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    account = await auth_service.authenticate_account(
        form_data.username, form_data.password
    )
    if not account:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": account.public_id, "role": account.role}
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/account")
async def get_account(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = decode_access_token(token)
        public_id = payload.get("sub")
        role = payload.get("role")
        account = await auth_service.get_account_by_public_id(public_id)
        if account:
            return {
                "account_id": account.public_id,
                "username": account.username,
                "role": role,
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.delete("/account")
async def delete_account(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = decode_access_token(token)
        public_id = payload.get("sub")
        account = await auth_service.get_account_by_public_id(public_id)
        if account:
            deleted = await auth_service.delete_account(account)
            producer.send_and_wait(
                topic, value=create_account_stream_event("account_deleted", deleted)
            )
            return {"status": "Account deleted"}
        else:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.put("/account")
async def update_account(
    token: Annotated[str, Depends(oauth2_scheme)],
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    try:
        payload = decode_access_token(token)
        public_id = payload.get("sub")
        account = await auth_service.get_account_by_public_id(public_id)
        if account:
            account.encrypted_password = hash_password(form_data.password)
            updated = await auth_service.update_account(account)
            producer.send_and_wait(
                topic, value=create_account_stream_event("account_updated", updated)
            )
            return {"status": "Account updated"}
        else:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.post("/verify")
async def verify(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = decode_access_token(token)
        public_id = payload.get("sub")
        account = await auth_service.get_account_by_public_id(public_id)
        if account:
            return {"status": "Token is valid"}
        else:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
