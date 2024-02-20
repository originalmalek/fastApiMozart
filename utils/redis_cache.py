from fastapi_cache.decorator import cache

from trades.errors import raise_conflict_error

import cryptocompare

from utils.bybit_api import get_instruments_info


@cache(expire=60*60*24, namespace='cryptocompare_exchanges')  # Caching for 24 hours
async def get_exchanges_from_cryptocompare():
    response = cryptocompare.get_exchanges()
    if not response:
        raise_conflict_error(message='Server error. Try your request later')
    return response


@cache(expire=60*60*24, namespace='all_exchange_pairs')
async def get_cached_instruments(api_key: str, api_secret: str, symbol: str = None):
    return get_instruments_info(api_secret=api_secret, api_key=api_key, symbol=symbol)['result']['list']