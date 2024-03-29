from fastapi import HTTPException, Header, status, Depends
from typing import Annotated
import jwt
from jwt.exceptions import DecodeError, ExpiredSignatureError
from passlib.context import CryptContext
from datetime import datetime, timedelta

from config import settings
from . import db_queries
from .schemas import User


middleware_key = settings.MIDDLEWARE_KEY
algorithm_key = settings.ALGORITHM_KEY
algorithm = settings.ALGORITHM
access_token_expire = settings.ACCESS_TOKEN_EXPIRES
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_user(username, password):
    return await db_queries.create_user(password=pwd_context.hash(password), username=username)

async def validate_user(token: Annotated[str, Header()]):
    try:
        decrypted_user_data = jwt.decode(token, key=algorithm_key, algorithms=algorithm)
    except DecodeError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail={'status': 'error', 'message': 'Invalid token'})
    except ExpiredSignatureError:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail={'status': 'error', 'message': 'Token expired'})
    user = await db_queries.get_user_by_user_id(decrypted_user_data['user_id'])
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail={'status': 'error', 'message': 'Invalid credentials'})
    return user


async def create_token(username: str, password: str):
    user = await db_queries.get_user_by_username(username)

    if user is None or not pwd_context.verify(password, user.password):
        return None, None

    expiration_time = datetime.utcnow() + timedelta(access_token_expire)
    token = jwt.encode({'user_id': user.id, 'exp': expiration_time}, key=algorithm_key, algorithm=algorithm)
    return token, expiration_time


async def check_exchange_keys(user: Annotated[User, Depends(validate_user)]):
    keys = await db_queries.get_exchange_keys(user.id)

    if keys is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail={'status': 'error', 'message': 'Keys not found'})
    return keys