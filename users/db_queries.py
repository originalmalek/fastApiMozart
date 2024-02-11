from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound, IntegrityError
from .models import User, ExchangeKeys
from database import async_session

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

async def get_exchange_keys(user_id):
    async with async_session.begin() as session:
        result = await session.execute(select(ExchangeKeys).filter_by(user_id=user_id))
        keys = result.scalar_one_or_none()
        return keys

async def update_exchange_keys(api_key, api_secret, user_id):
    async with async_session.begin() as session:
        try:
            result = await session.execute(select(ExchangeKeys).filter_by(user_id=user_id))
            keys = result.scalar_one()
            keys.api_key = api_key
            keys.api_secret = api_secret
        except NoResultFound:
            keys = ExchangeKeys(api_key=api_key, api_secret=api_secret, user_id=user_id)
            session.add(keys)
        await session.commit()
        return True