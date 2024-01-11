from sqlalchemy.exc import IntegrityError, NoResultFound

from database import session
from .models import User, ExchangeKeys


async def create_user(password, username):
    try:
        new_user = User(password=password, username=username)
        session.add(new_user)
        session.commit()
        return True
    except IntegrityError:
        session.rollback()
        return False

async def get_user_by_username(username):
    user = session.query(User).filter(User.username == username).first()
    return user


async def get_exchange_keys(user_id):
    keys = session.query(ExchangeKeys).filter(ExchangeKeys.id_user == user_id).one_or_none()
    return keys



async def update_exchange_keys(api_key, api_secret, user_id):
    try:
        keys = session.query(ExchangeKeys).filter(ExchangeKeys.id_user == user_id).one()
        keys.api_key = api_key
        keys.api_secret = api_secret
        session.commit()
        return True
    except NoResultFound:
        keys = ExchangeKeys(api_key=api_key, api_secret=api_secret, id_user=user_id)
        session.add(keys)
        session.commit()
        return True
    except IntegrityError:
        session.rollback()
        return False
