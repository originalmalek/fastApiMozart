from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from config import settings

if settings.MODE == 'TEST':
    database_url = settings.DATABASE_TEST_URL
    DATABASE_PARAMS = {'poolclass': NullPool}
else:
    database_url = settings.DATABASE_URL
    DATABASE_PARAMS = {}
async_engine = create_async_engine(database_url, **DATABASE_PARAMS)

async_session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass