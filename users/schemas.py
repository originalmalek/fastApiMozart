from pydantic import BaseModel, Extra


class User(BaseModel, extra=Extra.forbid):
    password: str
    username: str


class ExchangeKeys(BaseModel, extra=Extra.forbid):
    api_key: str
    api_secret: str
