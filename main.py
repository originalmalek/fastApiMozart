import logging
from starlette.middleware.sessions import SessionMiddleware
from fastapi import FastAPI

from users.dependencies import middleware_key
from website.router import website
from users.router import users
from trades.router import trades


app = FastAPI()

logging.basicConfig(format='%(asctime)s %(levelname)s:%(name)s:%(message)s', level=logging.DEBUG)
app.add_middleware(SessionMiddleware, secret_key=middleware_key)

app.include_router(users)
app.include_router(trades)
app.include_router(website)
