from typing import Annotated

import cryptocompare
from fastapi import Depends, APIRouter, Query
from pybit.exceptions import FailedRequestError, InvalidRequestError
from pydantic import constr

from schemas import Signal, Symbol, StopLoss
from trades.errors import raise_conflict_error, raise_unauthorized_error
from users.dependencies import validate_user, check_exchange_keys
from users.schemas import User, ExchangeKeys
from utils import mozart_deal, bybit_api
from utils.utilities import get_exchanges_from_cryptocompare

trades = APIRouter(prefix='/api', tags=['Trades'])


@trades.delete('/trade')
async def cancel_trade(symbol: Symbol, keys: Annotated[ExchangeKeys, Depends(check_exchange_keys)]):
    try:
        response = mozart_deal.cancel_trade(symbol=symbol.symbol, api_key=keys.api_key, api_secret=keys.api_secret)
    except FailedRequestError:
        raise_unauthorized_error()
    except InvalidRequestError as e:
        raise_conflict_error(message=e.message)
    if response is False:
        raise_conflict_error(message='Trade is not open')

    return {'status': 'success', 'message': 'Trade is cancelled'}


@trades.post('/sl_breakeven')
async def set_sl_breakeven(symbol: Symbol, keys: Annotated[ExchangeKeys, Depends(check_exchange_keys)]):
    try:
        response = mozart_deal.set_sl_breakeven(symbol=symbol.symbol, api_key=keys.api_key, api_secret=keys.api_secret)
    except FailedRequestError:
        raise_unauthorized_error()
    except InvalidRequestError as e:
        raise_conflict_error(message=e.message)

    if response is False:
        raise_conflict_error(message='SL Breakeven is not set')

    return {'status': 'success', 'message': 'SL Breakeven is set'}


@trades.delete('/add_orders')
async def set_sl_breakeven(symbol: Symbol, keys: Annotated[ExchangeKeys, Depends(check_exchange_keys)]):
    try:
        response = mozart_deal.cancel_add_orders(symbol=symbol.symbol, api_key=keys.api_key, api_secret=keys.api_secret)
    except FailedRequestError:
        raise_unauthorized_error()
    except InvalidRequestError as e:
        raise_conflict_error(message=e.message)

    if response is False:
        raise_conflict_error(message='Add orders not canceled')

    return {'status': 'success', 'message': 'Add orders are canceled'}


@trades.get('/position')
async def get_positions(keys: Annotated[ExchangeKeys, Depends(check_exchange_keys)],
                        symbol: constr(min_length=1) = Query(...)):
    try:
        response = bybit_api.get_position_info(symbol=symbol, api_key=keys.api_key, api_secret=keys.api_secret)
    except FailedRequestError:
        raise_unauthorized_error()
    except InvalidRequestError as e:
        raise_conflict_error(message=e.message)
    if response is False:
        raise_conflict_error(message='Get position error')

    return {'status': 'success', 'message': response}


@trades.get('/positions')
async def get_positions(keys: Annotated[ExchangeKeys, Depends(check_exchange_keys)]):
    try:
        response = bybit_api.get_position_info(api_key=keys.api_key, api_secret=keys.api_secret)
    except FailedRequestError:
        raise_unauthorized_error()
    except InvalidRequestError as e:
        raise_conflict_error(message=e.message)
    if response is False:
        raise_conflict_error(message='Get position error')

    return {'status': 'success', 'message': response}


@trades.post('/trade')
async def create_trade(signal: Signal, keys: Annotated[ExchangeKeys, Depends(check_exchange_keys)]):
    try:
        mozart_deal.create_trade(trade=signal, api_key=keys.api_key, api_secret=keys.api_secret)
    except FailedRequestError:
        raise_unauthorized_error()
    except InvalidRequestError as e:
        raise_conflict_error(message=f'Trade is not created{e.message}')

    return {'status': 'success', 'message': 'Trade is created'}


@trades.get("/prices")
async def get_prices(user: Annotated[User, Depends(validate_user)], coins_from: constr(min_length=1) = Query(...),
                     coins_to: constr(min_length=1) = Query(...), ):
    response = cryptocompare.get_price(coins_from, coins_to)
    if not response:
        raise_conflict_error(message='Incorrect data')

    return {'status': 'success', 'message': response}


@trades.get('/exchanges')
async def exchanges(user: Annotated[User, Depends(validate_user)]):
    response = await get_exchanges_from_cryptocompare()
    return {'status': 'success', 'message': response}


@trades.post('/stoploss')
def set_stop_loss(sl_data: StopLoss, keys: Annotated[ExchangeKeys, Depends(check_exchange_keys)]):
    symbol = sl_data.symbol
    stop_price = sl_data.stop_price
    try:
        api_key = keys.api_key
        api_secret = keys.api_secret
        position = bybit_api.get_position_info(symbol=symbol, api_secret=api_secret, api_key=api_key)
        bybit_api.trading_stop(symbol=symbol, sl_price=stop_price, api_key=api_key, api_secret=api_secret,
                               sl_size=position['result']['list'][0]['size'])
    except FailedRequestError:
        raise_unauthorized_error()
    except InvalidRequestError as e:
        raise_conflict_error(message=e.message)

    return {'status': 'success', 'message': 'stop price updated'}
