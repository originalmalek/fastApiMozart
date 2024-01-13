from typing import Optional

from fastapi import Form, Request, APIRouter, status
from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pybit.exceptions import FailedRequestError, InvalidRequestError

import users.dependencies
import users.router
import users.schemas
from users import db_queries
from users.db_queries import update_exchange_keys
from utils import mozart_deal
from utils.bybit_api import get_position_info, get_tickers, trading_stop, open_order, get_instruments_info

website = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory='templates')


def put_session_message(request, status, message):
    request.session['status'] = status
    request.session['message'] = message


def redirect(url, status_code, request=None, status=None, message=None, delete_cookie=None):
    if status:
        put_session_message(request, status, message)

    response = RedirectResponse(url=url, status_code=status_code)

    if delete_cookie:
        response.delete_cookie(key='access_token')

    return response


async def get_exchange_keys(request: Request):
    access_token = request.cookies.get('access_token')
    user = await users.dependencies.validate_user(access_token)
    keys = await db_queries.get_exchange_keys(user.id)
    return keys


async def get_sorted_positions(api_key, api_secret, settle_coin='USDT'):
    positions = get_position_info(api_key=api_key, api_secret=api_secret, settle_coin=settle_coin)
    return sorted(positions['result']['list'], key=lambda d: d['symbol'])


@website.get('/')
async def create_user(request: Request):
    access_token = request.cookies.get('access_token')
    if access_token:
        return RedirectResponse('/panel', status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse('register.html',
                                      {'request': request, 'status': request.session.pop('status', None),
                                       'message': request.session.pop('message', None), 'is_public_page': True})


@website.post("/register_form")
async def register(request: Request, username: str = Form(...), password: str = Form(...)):
    print(username, password)
    created = await users.dependencies.create_user(password=password, username=username)
    if not created:
        return redirect(url='/', status_code=status.HTTP_303_SEE_OTHER, request=request, status='error',
                        message='User exists', delete_cookie=True)

    token, _ = await users.dependencies.create_token(username, password)

    response = redirect(url='/exchange_keys', status_code=status.HTTP_302_FOUND, request=request, status='success',
                        message='User successfully created. Please add your Bybit exchange keys')

    response.set_cookie(key='access_token', value=token)
    return response


@website.post("/login")
async def login_user(request: Request, username: str = Form(...), password: str = Form(...)):
    token, _ = await users.dependencies.create_token(username, password)
    if token is None:
        return redirect(url='/login', status_code=status.HTTP_302_FOUND, request=request, status='error',
                        message='Wrong login or password', delete_cookie=True)

    response = RedirectResponse('/panel', status_code=status.HTTP_302_FOUND)
    response.set_cookie(key='access_token', value=token, httponly=True)
    return response


@website.get("/login")
async def login(request: Request):
    access_token = request.cookies.get('access_token')

    try:
        await users.dependencies.validate_user(token=access_token)
        return RedirectResponse('/panel', status_code=status.HTTP_302_FOUND)
    except:
        response = templates.TemplateResponse('login.html',
                                              {'request': request, 'status': request.session.pop('status', None),
                                               'message': request.session.pop('message', None), 'is_public_page': True})
        response.delete_cookie('access_token')
        return response


@website.get("/exchange_keys")
async def exchange_keys_page(request: Request):
    access_token = request.cookies.get('access_token')
    if not access_token:
        return redirect(url='/login', status_code=status.HTTP_302_FOUND, request=request, status='error',
                        message='Please login to the panel', delete_cookie=True)
    try:
        await users.dependencies.validate_user(token=access_token)
        return templates.TemplateResponse('exchange_keys.html',
                                          {'request': request, 'status': request.session.pop('status', None),
                                           'message': request.session.pop('message', None)}, )
    except HTTPException:
        return redirect(url='/login', status_code=status.HTTP_302_FOUND, request=request, status='error',
                        message='Session is expired', delete_cookie=True)


@website.get("/logout")
async def logout(request: Request):
    return redirect(url='/login', status_code=status.HTTP_302_FOUND, request=request, status='success',
                    message='Logout successful', delete_cookie=True)


@website.get('/panel')
async def show_panel(request: Request):
    try:
        keys = await get_exchange_keys(request)
        api_key = keys.api_key
        api_secret = keys.api_secret
        positions = await get_sorted_positions(api_key, api_secret)
        instruments = get_instruments_info(api_secret=api_secret, api_key=api_key, symbol=None)['result']['list']

        total_unrealised_pnl = 0
        total_realised_pnl = 0

        for position in positions:
            unrealised_pnl = float(position['unrealisedPnl'])
            realised_pnl = float(position['cumRealisedPnl'])
            total_unrealised_pnl += unrealised_pnl
            total_realised_pnl += realised_pnl
        return templates.TemplateResponse('panel.html', {'request': request, 'positions': positions,
                                                         'unrealised_pnl': round(total_unrealised_pnl, 2),
                                                         'realised_pnl': round(total_realised_pnl, 2),
                                                         'instruments': instruments,
                                                         'status': request.session.pop('status', None),
                                                         'message': request.session.pop('message', None)})
    except HTTPException:
        return redirect(url='/exchange_keys', status_code=status.HTTP_303_SEE_OTHER, request=request, status='error',
                        message='Keys are not added. Please add your Bybit API keys', delete_cookie=None)

    except FailedRequestError:
        return redirect(url='/exchange_keys', status_code=status.HTTP_302_FOUND, request=request, status='error',
                        message='Keys are not valid. Please update your Bybit API keys', delete_cookie=None)

    except InvalidRequestError:
        return redirect(url='/exchange_keys', status_code=status.HTTP_302_FOUND, request=request, status='error',
                        message='Wrong request to Bybit API, Please update your Bybit API keys', delete_cookie=None)


@website.post("/exchange_keys")
async def register(request: Request, api_key: str = Form(...), api_secret: str = Form(...)):
    access_token = request.cookies.get('access_token')

    try:
        user = await users.dependencies.validate_user(token=access_token)
        print(user.id)
        await update_exchange_keys(api_key=api_key, api_secret=api_secret, user_id=user.id)
        return redirect(url='/panel', status_code=status.HTTP_302_FOUND, request=request, status='success',
                        message='Keys are updated')

    except HTTPException:
        return redirect(url='/exchange_keys', status_code=status.HTTP_302_FOUND, request=request, status='error',
                        message='Keys are not updated')


@website.get("/exchange_keys")
async def exchange_keys_page(request: Request):
    access_token = request.cookies.get('access_token')
    try:
        await users.dependencies.validate_user(token=access_token)
        return templates.TemplateResponse('exchange_keys.html',
                                          {'request': request, 'status': request.session.pop('status', None),
                                           'message': request.session.pop('message', None)}, )
    except HTTPException:
        return redirect(url='/login', status_code=status.HTTP_302_FOUND, request=request, status='error',
                        message='Session expired', delete_cookie=True)


@website.post('/form_create_trade')
async def process_form_data(request: Request, inputField: str = Form(default=None)):
    if not inputField:
        return redirect(url=f'/panel', status_code=status.HTTP_302_FOUND, request=request, status='error',
                        message='Trade is not created. Please input trade details')

    try:
        keys = await get_exchange_keys(request)
        trade = eval(inputField)
        mozart_deal.create_trade(trade, api_key=keys.api_key, api_secret=keys.api_secret)
        return redirect(url=f'/panel', status_code=status.HTTP_302_FOUND, request=request, status='success',
                        message=f'Trade successfully created {trade["symbol"]}')

    except HTTPException:
        return redirect(url='/login', status_code=status.HTTP_302_FOUND, request=request, status='error',
                        message='Session is expired', delete_cookie=True)

    except FailedRequestError:
        return redirect(url='/exchange_keys', status_code=status.HTTP_302_FOUND, request=request, status='error',
                        message='Keys are not valid. Please update your Bybit API keys')

    except InvalidRequestError:
        return redirect(url=f'/panel', status_code=status.HTTP_302_FOUND, request=request, status='error',
                        message=f'Trade is not created {trade["symbol"]}')

    except KeyError:
        return redirect(url=f'/panel', status_code=status.HTTP_302_FOUND, request=request, status='error',
                        message=f'Trade is not created. Write correct data to create trade.')

    except NameError:
        return redirect(url=f'/panel', status_code=status.HTTP_302_FOUND, request=request, status='error',
                        message=f'Trade is not created. Write correct data to create trade.')

    except TypeError:
        return redirect(url=f'/panel', status_code=status.HTTP_302_FOUND, request=request, status='error',
                        message=f'Trade is not created. Write correct data to create trade.')


@website.post('/submit')
async def process_form_data(request: Request):
    form_data = await request.form()
    input_field_value = eval(form_data.get('myData'))
    action = input_field_value['action']
    symbol = input_field_value['symbol']
    page = input_field_value.get('page', symbol)
    try:
        keys = await get_exchange_keys(request)
        api_key = keys.api_key
        api_secret = keys.api_secret
    except HTTPException:
        return redirect(url=f'/login', status_code=status.HTTP_302_FOUND, request=request, status='error',
                        message='Session is expired', delete_cookie=True)

    try:
        if action == 'cancel_trade':
            response = mozart_deal.cancel_trade(symbol=symbol, api_key=api_key, api_secret=api_secret)
            message = f'Trade successfully canceled {symbol}'

        if action == 'set_sl_breakeven':
            response = mozart_deal.set_sl_breakeven(symbol=symbol, api_key=api_key, api_secret=api_secret)
            message = f'Stoploss successfully set to breakeven {symbol}'

        if action == 'cancel_add_orders':
            response = mozart_deal.cancel_add_orders(symbol=symbol, api_key=api_key, api_secret=api_secret)
            message = f'Add orders successfully canceled {symbol}'

        if response:
            return redirect(url=f'/{page}', status_code=status.HTTP_302_FOUND, request=request, status='success',
                            message=message)

    except FailedRequestError:
        return redirect(url='/exchange_keys', status_code=status.HTTP_302_FOUND, request=request, status='error',
                        message='Keys are not valid. Please update your Bybit API keys')

    except InvalidRequestError as err:
        return redirect(url=f'/{page}', status_code=status.HTTP_302_FOUND, request=request, status='error',
                        message=f'Wrong request to Bybit API {err.message}')

    return redirect(url=f'/{page}', status_code=status.HTTP_302_FOUND, request=request, status='error',
                    message='The trade is not open')


@website.post('/set_stop')
async def set_stop(request: Request, stop_price: str = Form(default=None), symbol: str = Form(...)):
    if not set_stop:
        return redirect(url=f'/{symbol}', status_code=status.HTTP_302_FOUND, request=request, status='error',
                        message='StopLoss is not updated. Please write a number.')
    try:
        stop_price = float(stop_price)
        keys = await get_exchange_keys(request)
        api_key = keys.api_key
        api_secret = keys.api_secret
        position = get_position_info(symbol=symbol, api_secret=api_secret, api_key=api_key)
        trading_stop(symbol=symbol, sl_price=stop_price, api_key=api_key, api_secret=api_secret,
                     sl_size=position['result']['list'][0]['size'])

        return redirect(url=f'/{symbol}', status_code=status.HTTP_302_FOUND, request=request, status='success',
                        message='StopLoss successfully updated.')

    except ValueError:
        return redirect(url=f'/{symbol}', status_code=status.HTTP_302_FOUND, request=request, status='error',
                        message='StopLoss is not updated. Please write a number.')

    except FailedRequestError as err:
        return redirect(url='/exchange_keys', status_code=status.HTTP_302_FOUND, request=request, status='error',
                        message=f'Keys are not valid. Please update your Bybit API keys\n {err.message}')

    except InvalidRequestError as err:
        return redirect(url=f'/{symbol}', status_code=status.HTTP_302_FOUND, request=request, status='error',
                        message=f'Wrong request to Bybit API {err.message}')

    except:
        return redirect(url=f'/{symbol}', status_code=status.HTTP_302_FOUND, request=request, status='error',
                        message='StopLoss is not updated.')


@website.get("/{symbol}")
async def open_trade_page(request: Request, symbol: str):
    try:
        keys = await get_exchange_keys(request)
        api_key = keys.api_key
        api_secret = keys.api_secret
        position = get_position_info(api_key=api_key, api_secret=api_secret, symbol=symbol)['result']['list']
        ticker = get_tickers(symbol=symbol, api_key=api_key, api_secret=api_secret)
        return templates.TemplateResponse('pair.html', {'request': request, 'positions': position,
                                                        'ticker': ticker['result']['list'][0], 'position': position[0],
                                                        'status': request.session.pop('status', None),
                                                        'message': request.session.pop('message', None)})

    except HTTPException:
        return redirect(url='/exchange_keys', status_code=status.HTTP_302_FOUND, request=request, status='error',
                        message='Keys are not added. Please add your Bybit API keys')

    except FailedRequestError as err:
        return redirect(url='/exchange_keys', status_code=status.HTTP_302_FOUND, request=request, status='error',
                        message=f'Keys are not valid. Please update your Bybit API keys {err.message}',
                        delete_cookie=None)

    except InvalidRequestError as err:
        return redirect(url=f'/panel', status_code=status.HTTP_302_FOUND, request=request, status='error',
                        message=f'Wrong request to Bybit API {err.message}')


@website.post("/market_position")
async def analyze(request: Request,
                  quantity: Optional[str] = Form(default=None),
                  side_symbol: Optional[str] = Form(...)):
    try:
        keys = await get_exchange_keys(request)
        side, symbol = side_symbol.split('_')

        open_order(symbol=symbol, side=side,
                   order_type='Market',
                   quantity=quantity,
                   api_key=keys.api_key,
                   api_secret=keys.api_secret)

        return redirect(url=f'/{symbol}', status_code=status.HTTP_302_FOUND, request=request, status='success',
                        message=f'Order successfully placed {symbol}')

    except HTTPException:
        return redirect(url='/exchange_keys', status_code=status.HTTP_302_FOUND, request=request, status='error',
                        message='Keys are not added. Please add your Bybit API keys')

    except FailedRequestError as err:
        return redirect(url='/exchange_keys', status_code=status.HTTP_302_FOUND, request=request, status='error',
                        message=f'Keys are not valid. Please update your Bybit API keys\n {err.message}')

    except InvalidRequestError as err:
        return redirect(url=f'/{symbol}', status_code=status.HTTP_302_FOUND, request=request, status='error',
                        message=f'Wrong request to Bybit API {err.message}')
