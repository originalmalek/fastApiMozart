from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from environs import Env

env = Env()
env.read_env()

async_engine = create_async_engine(env('DATABASE_URL'))

async_session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass