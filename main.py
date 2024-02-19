import logging
from starlette.middleware.sessions import SessionMiddleware
from fastapi import FastAPI

from users.dependencies import middleware_key
from website.router import website
from users.router import users
from trades.router import trades

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend


from redis import asyncio as aioredis

app = FastAPI()

logging.basicConfig(format='%(asctime)s %(levelname)s:%(name)s:%(message)s', level=logging.DEBUG)
app.add_middleware(SessionMiddleware, secret_key=middleware_key)

app.include_router(users)
app.include_router(trades)
app.include_router(website)


@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost:6379")
    FastAPICache.init(RedisBackend(redis), prefix="cache")