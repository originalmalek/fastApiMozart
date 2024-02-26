from pydantic import BaseModel, Extra, constr


class User(BaseModel, extra=Extra.forbid):
    username: constr(min_length=2)
    password: constr(min_length=2)


class ExchangeKeys(BaseModel, extra=Extra.forbid):
    api_key: constr(min_length=2)
    api_secret: constr(min_length=2)

