import asyncio

import pytest
import json

import pytest_asyncio
from sqlalchemy import insert

from config import settings
from database import Base, async_engine, async_session
from main import app as fastapi_app
from users.models import ExchangeKeys, User

from httpx import AsyncClient

@pytest_asyncio.fixture(autouse=True, scope='session')
async def prepare_database():
    assert settings.MODE == 'TEST'
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    def open_mock_json(model: str):
        with open(f'tests/mock_{model}.json') as file:
            return json.load(file)

    users = open_mock_json('user')
    # exchange_keys = open_mock_json('exchange_keys')

    async with async_session() as session:
        add_users = insert(User).values(users)
        await session.execute(add_users)
        await session.commit()


@pytest_asyncio.fixture(scope="session")
def event_loop(request):
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='function')
async def ac():
    async with AsyncClient(app=fastapi_app, base_url='http://test') as ac:
        yield ac