import logging

from fastapi import FastAPI


from website.router import website
from users.router import users
from trades.router import trades

app = FastAPI()

logging.basicConfig(format='%(asctime)s %(levelname)s:%(name)s:%(message)s', level=logging.DEBUG)

app.include_router(users)
app.include_router(trades)
app.include_router(website)
