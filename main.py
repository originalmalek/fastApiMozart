import logging

from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi import FastAPI

from config import settings
from users.dependencies import middleware_key
from website.router import website
from users.router import users
from trades.router import trades

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend


from redis import asyncio as aioredis

app = FastAPI(ssl_keyfile=settings.SSL_KEY_FILE_NAME,
              ssl_certfile=settings.SSL_CERTIFICATE_FILE_NAME)

origins = ['http://localhost',
           'http://www.ttrader.top',
           'http://ttrader.top/',
           'https://www.ttrader.top',
           'https://ttrader.top/',
           'http://213.183.59.189',
           'http://127.0.0.1',
           '127.0.0.1']

methods = ['GET', 'POST', 'PATCH', 'PUT']

headers = ['Content-Type',
           'Set-Cookie',
           'Access-Control-Allow-Headers',
           'Access-Control-Allow-Origin',
           'Authorization']

logging.basicConfig(format='%(asctime)s %(levelname)s:%(name)s:%(message)s', level=logging.DEBUG)
app.add_middleware(SessionMiddleware, secret_key=middleware_key)

app.add_middleware(CORSMiddleware,
                   allow_origins=origins,
                   allow_credentials=True,
                   allow_methods=methods,
                   allow_headers=headers)

app.include_router(users)
app.include_router(trades)
app.include_router(website)

@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost:6379")
    FastAPICache.init(RedisBackend(redis), prefix="cache")
