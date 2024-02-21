from copy import deepcopy

from sqlalchemy.exc import NoResultFound, IntegrityError
from sqlalchemy.future import select

from database import async_session
from utils.utils import decrypt_data, encrypt_data
from .models import User, ExchangeKeys


async def create_user(password, username):
    try:
        async with async_session.begin() as session:
            new_user = User(password=password, username=username)
            session.add(new_user)
            await session.commit()
            return True
    except IntegrityError:
        await session.rollback()
        return False


async def get_user_by_username(username):
    async with async_session.begin() as session:
        result = await session.execute(select(User).filter_by(username=username))
        user = result.scalar_one_or_none()
        return user


async def get_user_by_user_id(user_id):
    async with async_session.begin() as session:
        result = await session.execute(select(User).filter_by(id=user_id))
        user = result.scalar_one_or_none()
        return user


async def update_exchange_keys(api_key, api_secret, user_id):
    encrypted_api_key = encrypt_data(api_key)
    encrypted_api_secret = encrypt_data(api_secret)
    async with async_session.begin() as session:
        try:
            result = await session.execute(select(ExchangeKeys).filter_by(user_id=user_id))
            keys = result.scalar_one()
            keys.api_key = encrypted_api_key
            keys.api_secret = encrypted_api_secret
        except NoResultFound:
            keys = ExchangeKeys(api_key=encrypted_api_key, api_secret=encrypted_api_secret, user_id=user_id)
            session.add(keys)
        await session.commit()
        return True


async def get_exchange_keys(user_id):
    async with async_session.begin() as session:
        result = await session.execute(select(ExchangeKeys).filter_by(user_id=user_id))
        keys = result.scalar_one_or_none()
        if keys:
            decrypted_keys = deepcopy(keys)  # creates a deep copy of keys
            decrypted_keys.api_key = decrypt_data(keys.api_key)
            decrypted_keys.api_secret = decrypt_data(keys.api_secret)
            return decrypted_keys
        return keys
