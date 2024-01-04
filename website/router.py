from fastapi import Form, Request, APIRouter, status
from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pybit.exceptions import FailedRequestError, InvalidRequestError

import users.dependencies
import users.router
import users.schemas
from users.db_queries import update_exchange_keys
from utils import mozart_deal
from utils.bybit_api import get_position_info, get_tickers

website = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory='templates')


def put_session_message(request, status, message):
    request.session['status'] = status
    request.session['message'] = message


async def get_exchange_keys(request: Request):
    access_token = request.cookies.get('access_token')
    user = await users.dependencies.validate_user(access_token)
    keys = await users.dependencies.check_exchange_keys(user)
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
        put_session_message(request, status='error', message='User exists')

        response = RedirectResponse('/', status_code=status.HTTP_303_SEE_OTHER)
        response.delete_cookie(key='access_token')
        return response
    token, _ = await users.dependencies.create_token(username, password)
    put_session_message(request, status='success',
                        message='User successfully created. Please add your Bybit exchange keys')

    response = RedirectResponse('/exchange_keys', status_code=status.HTTP_302_FOUND)
    response.set_cookie(key='access_token', value=token)
    return response


@website.post("/login")
async def login_user(request: Request, username: str = Form(...), password: str = Form(...)):
    token, _ = await users.dependencies.create_token(username, password)
    if token is None:
        put_session_message(request, status='error', message='Wrong login or password')

        response = RedirectResponse('/login', status_code=status.HTTP_303_SEE_OTHER)
        response.delete_cookie(key='access_token')
        return response
    response = RedirectResponse('/panel', status_code=status.HTTP_302_FOUND)
    response.set_cookie(key='access_token', value=token)
    return response


@website.get("/login")
async def login(request: Request):
    access_token = request.cookies.get('access_token')

    try:
        await users.dependencies.validate_user(token=access_token)
        response = RedirectResponse('/panel', status_code=status.HTTP_302_FOUND)
        return response
    except:
        response = templates.TemplateResponse('login.html',
                                              {'request': request, 'status': request.session.pop('status', None),
                                               'message': request.session.pop('message', None), 'is_public_page': True})
        response.delete_cookie('access_token')
        return response


@website.get("/exchange_keys")
async def exchange_keys_page(request: Request):
    access_token = request.cookies.get('access_token')
    try:
        await users.dependencies.validate_user(token=access_token)
        return templates.TemplateResponse('exchange_keys.html',
                                          {'request': request, 'status': request.session.pop('status', None),
                                           'message': request.session.pop('message', None)}, )
    except HTTPException:
        put_session_message(request, status='error', message='Session is expired')

        response = RedirectResponse('/login', status_code=status.HTTP_302_FOUND)
        response.delete_cookie(key='access_token')
        return response


@website.get("/logout")
async def logout(request: Request):
    put_session_message(request, status='success', message='Logout successful')
    response = RedirectResponse('/login', status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key='access_token')
    return response


@website.get('/panel')
async def show_panel(request: Request):
    try:
        keys = await get_exchange_keys(request)
        positions = await get_sorted_positions(keys.api_key, keys.api_secret)
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
                                                         'status': request.session.pop('status', None),
                                                         'message': request.session.pop('message', None)})
    except HTTPException:
        put_session_message(request, status='error', message='Keys are not added. Please add your Bybit API keys')
        response = RedirectResponse(f'/exchange_keys', status_code=status.HTTP_303_SEE_OTHER)

    except FailedRequestError:
        put_session_message(request, status='error', message='Keys are not valid. Please update your Bybit API keys')
        response = RedirectResponse(f'/exchange_keys', status_code=status.HTTP_302_FOUND)

    except InvalidRequestError:
        put_session_message(request, status='error',
                            message='Wrong request to Bybit API, Please update your Bybit API keys')
        response = RedirectResponse(f'/exchange_keys', status_code=status.HTTP_302_FOUND)

    return response


@website.post("/exchange_keys")
async def register(request: Request, api_key: str = Form(...), api_secret: str = Form(...)):
    access_token = request.cookies.get('access_token')

    try:
        user = await users.dependencies.validate_user(token=access_token)
        print(user.id)
        await update_exchange_keys(api_key=api_key, api_secret=api_secret, user_id=user.id)
        put_session_message(request, status='success', message='Keys are updated')

        return RedirectResponse('/exchange_keys', status_code=status.HTTP_302_FOUND)
    except HTTPException:
        put_session_message(request, status='error', message='Keys are not updated')

        response = RedirectResponse('/exchange_keys', status_code=status.HTTP_302_FOUND)
        return response


@website.get("/exchange_keys")
async def exchange_keys_page(request: Request):
    access_token = request.cookies.get('access_token')
    try:
        await users.dependencies.validate_user(token=access_token)
        return templates.TemplateResponse('exchange_keys.html',
                                          {'request': request, 'status': request.session.pop('status', None),
                                           'message': request.session.pop('message', None)}, )
    except HTTPException:
        put_session_message(request, status='error', message='Keys are updated')

        response = RedirectResponse('/login', status_code=status.HTTP_302_FOUND)
        response.delete_cookie(key='access_token')
        return response


@website.get("/{symbol}")
async def open_trade_page(request: Request, symbol: str):
    try:
        keys = await get_exchange_keys(request)
        api_key = keys.api_key
        api_secret = keys.api_secret
        position = get_position_info(api_key=api_key, api_secret=api_secret, symbol=symbol)['result']['list']
        ticker = get_tickers(symbol=symbol, api_key=api_key, api_secret=api_secret)
        return templates.TemplateResponse('pair.html', {'request': request, 'positions': position,
                                                        'ticker': ticker['result']['list'][0], 'position': position[0]})

    except HTTPException:
        put_session_message(request, status='error', message='Keys are not added. Please add your Bybit API keys')
        response = RedirectResponse(f'/exchange_keys', status_code=status.HTTP_302_FOUND)

    except FailedRequestError:
        put_session_message(request, status='error', message='Keys are not valid. Please update your Bybit API keys')
        response = RedirectResponse(f'/exchange_keys', status_code=status.HTTP_302_FOUND)

    except InvalidRequestError:
        put_session_message(request, status='error', message='Wrong request to Bybit API')
        response = RedirectResponse(f'/panel', status_code=status.HTTP_302_FOUND)

    return response


@website.post('/form_create_trade')
async def process_form_data(request: Request, inputField: str = Form(...)):
    try:
        keys = await get_exchange_keys(request)
        trade = eval(inputField)
        mozart_deal.create_trade(trade, api_key=keys.api_key, api_secret=keys.api_secret)
        put_session_message(request=request, status='success', message=f'Trade successfully created {trade["symbol"]}')
        return RedirectResponse('/panel', status_code=status.HTTP_302_FOUND)
    except HTTPException:
        put_session_message(request, status='error', message='Session is expired')

        response = RedirectResponse('/login', status_code=status.HTTP_302_FOUND)
        response.delete_cookie(key='access_token')
        return response

    except FailedRequestError:
        put_session_message(request, status='error', message='Keys are not valid. Please update your Bybit API keys')
        return RedirectResponse(f'/exchange_keys', status_code=status.HTTP_302_FOUND)

    except InvalidRequestError:
        put_session_message(request=request, status='error', message=f'Trade is not created {trade["symbol"]}')
        return RedirectResponse('/panel', status_code=status.HTTP_302_FOUND)




@website.post('/submit')
async def process_form_data(request: Request):
    form_data = await request.form()
    input_field_value = eval(form_data.get('myData'))
    action = input_field_value['action']
    symbol = input_field_value['symbol']

    try:
        keys = await get_exchange_keys(request)
        api_key = keys.api_key
        api_secret = keys.api_secret
    except HTTPException:
        put_session_message(request, status='error', message='Session is expired')

        response = RedirectResponse('/login', status_code=status.HTTP_302_FOUND)
        response.delete_cookie(key='access_token')
        return response

    try:
        if action == 'cancel_trade':
            response = mozart_deal.cancel_trade(symbol=symbol, api_key=api_key, api_secret=api_secret)
            put_session_message(request=request, status='success', message=f'Trade successfully canceled {symbol}')
        if action == 'set_sl_breakeven':
            response = mozart_deal.set_sl_breakeven(symbol=symbol, api_key=api_key, api_secret=api_secret)
            put_session_message(request=request, status='success',
                                message=f'Stoploss successfully set to breakeven {symbol}')
        if action == 'cancel_add_orders':
            response = mozart_deal.cancel_add_orders(symbol=symbol, api_key=api_key, api_secret=api_secret)
            put_session_message(request=request, status='success',
                                message=f'Add orders successfully canceled {symbol}')

    except FailedRequestError:
        put_session_message(request, status='error', message='Keys are not valid. Please update your Bybit API keys')
        return RedirectResponse(f'/exchange_keys', status_code=status.HTTP_302_FOUND)

    except InvalidRequestError:
        put_session_message(request, status='error', message='Wrong request to Bybit API')
        return RedirectResponse(f'/panel', status_code=status.HTTP_302_FOUND)


    if not response:
        put_session_message(request=request, status='error',
                            message=f'The trade is not open')
        return RedirectResponse('/panel', status_code=status.HTTP_302_FOUND)

    return RedirectResponse('/panel', status_code=status.HTTP_302_FOUND)