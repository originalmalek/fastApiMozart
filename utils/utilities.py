import base64

import cryptocompare
from cryptography.fernet import Fernet
from fastapi_cache.decorator import cache

from config import settings
from trades.errors import raise_conflict_error
from utils.bybit_api import get_instruments_info


key = settings.CRYPTOGRAPHY_KEY.encode()
cipher_suite = Fernet(key)


def encrypt_data(message):
    if message is not None:
        encoded_message = message.encode()
        encrypted_message = cipher_suite.encrypt(encoded_message)
        base64_encrypted_message = base64.urlsafe_b64encode(encrypted_message)
        return base64_encrypted_message.decode('utf-8')
    else:
        return None


def decrypt_data(encrypted_message):
    if encrypted_message is not None:
        base64_encrypted_message = encrypted_message.encode()
        decrypted_message = cipher_suite.decrypt(base64.urlsafe_b64decode(base64_encrypted_message))
        return decrypted_message.decode('utf-8')
    else:
        return None


@cache(expire=60 * 60 * 24, namespace='cryptocompare_exchanges')  # Caching for 24 hours
async def get_exchanges_from_cryptocompare():
    response = cryptocompare.get_exchanges()
    if not response:
        raise_conflict_error(message='Server error. Try your request later')
    return response


@cache(expire=60 * 60 * 24, namespace='all_exchange_pairs')
async def get_cached_instruments(api_key: str, api_secret: str, symbol: str = None):
    return get_instruments_info(api_secret=api_secret, api_key=api_key, symbol=symbol)['result']['list']
