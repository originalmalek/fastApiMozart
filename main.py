import time

import sentry_sdk

from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi import FastAPI
from starlette.requests import Request

from config import settings
from logger import logger
from users.dependencies import middleware_key
from website.router import website
from users.router import users
from trades.router import trades

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend


from redis import asyncio as aioredis


sentry_sdk.init(
    dsn="https://f20147196e18bc227a6e2fc28fcac07c@o4506815193350144.ingest.sentry.io/4506815194464256",
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,)

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


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info('Request execution time', extra={'process_time': round(process_time, 4)})
    return response