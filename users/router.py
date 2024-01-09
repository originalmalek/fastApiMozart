from typing import Annotated

from fastapi import Depends, HTTPException, status, APIRouter

from .dependencies import validate_user, create_user, create_token
from .schemas import User, ExchangeKeys
from users import db_queries

users = APIRouter(prefix='/api', tags=['Users'])


@users.get("/token")
async def get_token(user_data: User):
    user_username = user_data.username
    user_password = user_data.password

    token, expiration_time = await create_token(user_username, user_password)
    if token is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail={'status': 'error', 'message': 'Invalid credentials'})

    return {'status': 'success', 'token': token, 'exp_time': int(expiration_time.timestamp()),
            'token_type': 'bearer'}


@users.post('/register')
async def register_user(user_data: User):
    created = await create_user(user_data.username, user_data.password)
    if not created:
        raise HTTPException(status.HTTP_409_CONFLICT, detail={'status': 'error', 'message': 'User already exists'})
    return {'status': 'success', 'message': 'User successfully registered'}


@users.post('/keys')
async def update_keys(keys: ExchangeKeys, user: Annotated[User, Depends(validate_user)]):
    response = await db_queries.update_exchange_keys(api_key=keys.api_key, api_secret=keys.api_secret, user_id=user.id)
    if response is False:
        raise HTTPException(status.HTTP_409_CONFLICT, detail={'status': 'error', 'message': 'Keys are not updated'})

    return {'status': 'success', 'message': 'Keys are updated'}
