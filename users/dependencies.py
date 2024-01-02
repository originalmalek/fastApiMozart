from fastapi import HTTPException, Header, status, Depends
from environs import Env
from typing import Annotated
import jwt
from jwt.exceptions import DecodeError, ExpiredSignatureError
from passlib.context import CryptContext
from datetime import datetime, timedelta

from . import db_queries
from .schemas import User


env = Env()
env.read_env()

secret_key = env('SECRET_KEY')
algorithm = env('ALGORITHM')
access_token_expire = env.int('ACCESS_TOKEN_EXPIRES')
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_user(username, password):
    return await db_queries.create_user(password=pwd_context.hash(password), username=username)

async def validate_user(token: Annotated[str, Header()]):
    try:
        decrypted_user_data = jwt.decode(token, key=secret_key, algorithms=algorithm)
    except DecodeError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail={'status': 'error', 'message': 'Invalid token'})
    except ExpiredSignatureError:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail={'status': 'error', 'message': 'Token expired'})
    user = await db_queries.get_user_by_username(decrypted_user_data['username'])
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail={'status': 'error', 'message': 'Invalid credentials'})
    return user


async def create_token(username: str, password: str):
    user = await db_queries.get_user_by_username(username)

    if user is None or not verify_token(password, user.password):
        # TODO: raise custom Exception
        return None, None

    expiration_time = datetime.utcnow() + timedelta(access_token_expire)
    token = create_jwt_token(data={'username': username, 'exp': expiration_time})
    return token, expiration_time


def verify_token(plain_password, hash_password):
    return pwd_context.verify(plain_password, hash_password)


def create_jwt_token(data: dict):
    token = jwt.encode(data, key=secret_key, algorithm=algorithm)
    return token


async def check_exchange_keys(user: Annotated[User, Depends(validate_user)]):
    keys = await db_queries.get_exchange_keys(user.id)

    if keys is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail={'status': 'error', 'message': 'Keys not found'})
    return keys
