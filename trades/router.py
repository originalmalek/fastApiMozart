from typing import Annotated

import cryptocompare
from fastapi import Depends, APIRouter
from pybit.exceptions import FailedRequestError, InvalidRequestError

from users.dependencies import validate_user, check_exchange_keys
from users.schemas import User, ExchangeKeys
from trades.errors import raise_conflict_error
from schemas import Signal, Symbol, CoinsData
from utils import mozart_deal, bybit_api

trades = APIRouter()


@trades.post('/cancel_trade')
async def create_trade(symbol: Symbol, keys: Annotated[ExchangeKeys, Depends(check_exchange_keys)]):
    try:
        response = mozart_deal.cancel_trade(symbol=symbol.symbol, api_key=keys.api_key, api_secret=keys.api_secret)
    except FailedRequestError:
        raise_conflict_error(message='Failed access to the bybit API. Please update your keys')

    if response is False:
        raise_conflict_error(message='Trade is not canceled')

    return {'status': 'success', 'message': 'Trade is cancelled'}


@trades.post('/set_sl_breakeven')
async def set_sl_breakeven(symbol: Symbol, keys: Annotated[ExchangeKeys, Depends(check_exchange_keys)]):
    try:
        response = mozart_deal.set_sl_breakeven(symbol=symbol.symbol, api_key=keys.api_key, api_secret=keys.api_secret)
    except FailedRequestError:
        raise_conflict_error(message='Failed access to the bybit API. Please update your keys')

    if response is False:
        raise_conflict_error(message='SL Breakeven is not set')

    return {'status': 'success', 'message': 'SL Breakeven is set'}


@trades.post('/cancel_add_orders')
async def set_sl_breakeven(symbol: Symbol, keys: Annotated[ExchangeKeys, Depends(check_exchange_keys)]):
    try:
        response = mozart_deal.cancel_add_orders(symbol=symbol.symbol, api_key=keys.api_key, api_secret=keys.api_secret)
    except FailedRequestError:
        raise_conflict_error(message='Failed access to the bybit API. Please update your keys')

    if response is False:
        raise_conflict_error(message='Add orders not canceled')

    return {'status': 'success', 'message': 'Add orders are canceled'}


@trades.get('/get_position')
async def get_positions(symbol: Symbol, keys: Annotated[ExchangeKeys, Depends(check_exchange_keys)]):
    try:
        response = bybit_api.get_position_info(symbol=symbol.symbol, api_key=keys.api_key, api_secret=keys.api_secret)
    except FailedRequestError:
        raise_conflict_error(message='Failed access to the bybit API. Please update your keys')
    except InvalidRequestError:
        raise_conflict_error(message='Failed request to the exchange. Please check sends parameters')
    if response is False:
        raise_conflict_error(message='Get position error')

    return {'status': 'success', 'message': response}


@trades.get('/get_positions')
async def get_positions(keys: Annotated[ExchangeKeys, Depends(check_exchange_keys)]):
    try:
        response = bybit_api.get_position_info(api_key=keys.api_key, api_secret=keys.api_secret)
    except FailedRequestError:
        raise_conflict_error(message='Failed access to the bybit API. Please update your keys')
    except InvalidRequestError:
        raise_conflict_error(message='Failed request to the exchange. Please check sends parameters')
    if response is False:
        raise_conflict_error(message='Get position error')

    return {'status': 'success', 'message': response}

@trades.get('/get_position/{symbol}')
async def get_positions(symbol: str, keys: Annotated[ExchangeKeys, Depends(check_exchange_keys)]):
    try:
        response = bybit_api.get_position_info(symbol=symbol, api_key=keys.api_key, api_secret=keys.api_secret)
    except FailedRequestError:
        raise_conflict_error(message='Failed access to the bybit API. Please update your keys')
    except InvalidRequestError:
        raise_conflict_error(message='Failed request to the exchange. Please check sends parameters')
    if response is False:
        raise_conflict_error(message='Get position error')

    return {'status': 'success', 'message': response}


@trades.post('/create_trade')
async def create_trade(signal: Signal, keys: Annotated[ExchangeKeys, Depends(check_exchange_keys)]):
    try:
        response = mozart_deal.create_trade(trade=signal, api_key=keys.api_key, api_secret=keys.api_secret)
    except FailedRequestError:
        raise_conflict_error(message='Failed access to the bybit API. Please update your keys')

    if response is False:
        raise_conflict_error(message='Add orders not canceled')

    return {'status': 'success', 'message': 'Add orders are canceled'}


@trades.get('/get_prices')
async def get_price(coins_data: CoinsData, user: Annotated[User, Depends(validate_user)]):
    dir(cryptocompare)
    response = cryptocompare.get_price(coins_data.coins_from, coins_data.coins_to)
    if not response:
        raise_conflict_error(message='Incorrect data')

    return {'status': 'success', 'message': response}


@trades.get('/get_exchanges')
async def get_price(user: Annotated[User, Depends(validate_user)]):
    response = cryptocompare.get_exchanges()
    if not response:
        raise_conflict_error(message='Incorrect data')

    return {'status': 'success', 'message': response}
