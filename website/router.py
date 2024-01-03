from fastapi import Form, Request, APIRouter, status
from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pybit.exceptions import FailedRequestError, InvalidRequestError

import users.schemas
import users.dependencies
import users.router


from utils import mozart_deal
from utils.bybit_api import get_position_info, get_tickers

website = APIRouter()
templates = Jinja2Templates(directory='templates')


async def get_exchange_keys(request: Request):
    access_token = request.cookies.get('access_token')
    user = await users.dependencies.validate_user(access_token)
    keys = await users.dependencies.check_exchange_keys(user)
    return keys


async def get_sorted_positions(api_key, api_secret, settle_coin='USDT'):
    positions = get_position_info(api_key=api_key, api_secret=api_secret, settle_coin=settle_coin)
    return sorted(positions['result']['list'], key=lambda d: d['symbol'])


@website.post('/form_create_trade')
async def process_form_data(request: Request, inputField: str = Form(...)):
    print(inputField)
    try:
        keys = await get_exchange_keys(request)
        trade = eval(inputField)

        mozart_deal.create_trade(trade, api_key=keys.api_key, api_secret=keys.api_secret)
        return RedirectResponse('/panel', status_code=status.HTTP_302_FOUND)
    except:
        return RedirectResponse('/panel', status_code=status.HTTP_302_FOUND)


@website.post('/submit')
async def process_form_data(request: Request):
    form_data = await request.form()
    input_field_value = eval(form_data.get('myData'))
    action = input_field_value['action']
    symbol = input_field_value['symbol']

    keys = await get_exchange_keys(request)
    api_key = keys.api_key
    api_secret = keys.api_secret

    if action == 'cancel_trade':
        response = mozart_deal.cancel_trade(symbol=symbol, api_key=api_key, api_secret=api_secret)
        status = 'success'
    if action == 'set_sl_breakeven':
        response = mozart_deal.set_sl_breakeven(symbol=symbol, api_key=api_key, api_secret=api_secret)
        status = 'success'

    return RedirectResponse('/panel', status_code=status.HTTP_302_FOUND)


@website.get('/')
async def create_user(request: Request, params=None):
    if params is None:
        params = {'status': '', 'message': ''}
    token = request.cookies.get('access_token')
    if token:
        return RedirectResponse('/panel', status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse('register.html',
                                      {'request': request, 'status': params['status'], 'message': params['message']})


@website.post("/login")
async def login_user(request: Request, username: str = Form(...), password: str = Form(...)):
    token, _ = await users.dependencies.create_token(username, password)
    if token is None:
        response = templates.TemplateResponse('login.html', {'request': request, 'status': 'error',
                                                         'message': 'Wrong login or password'})
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
        response = templates.TemplateResponse('login.html', {'request': request,
                                                             'status': request.session.pop('status', None),
                                                             'message': request.session.pop('message', None)})
        response.delete_cookie('access_token')
        return response


@website.get("/logout")
async def logout(request: Request):
    access_token = request.cookies.get('access_token')
    if access_token:
        request.session['status'] = 'success'
        request.session['message'] = 'Logout successful'
        response = RedirectResponse('/login', status_code=status.HTTP_303_SEE_OTHER)
        response.delete_cookie(key='access_token')
        return response
    else:
        response = RedirectResponse('/login', status_code=status.HTTP_303_SEE_OTHER)
        response.delete_cookie(key='access_token')
        return response



@website.get('/panel')
async def show_panel(request: Request):
    try:
        keys = await get_exchange_keys(request)
        positions = await get_sorted_positions(keys.api_key, keys.api_secret)
    except HTTPException:
        response = RedirectResponse(f'/exchange_keys', status_code=status.HTTP_302_FOUND)
        return response
    except FailedRequestError:
        response = RedirectResponse(f'/exchange_keys', status_code=status.HTTP_302_FOUND)
        return response
    except InvalidRequestError:
        response = RedirectResponse(f'/exchange_keys', status_code=status.HTTP_302_FOUND)
        return response

    total_unrealised_pnl = 0
    total_realised_pnl = 0

    for position in positions:
        unrealised_pnl = float(position['unrealisedPnl'])
        realised_pnl = float(position['cumRealisedPnl'])
        total_unrealised_pnl += unrealised_pnl
        total_realised_pnl += realised_pnl
    return templates.TemplateResponse('panel.html', {'request': request, 'positions': positions,
                                                     'unrealised_pnl': round(total_unrealised_pnl, 2),
                                                     'realised_pnl': round(total_realised_pnl, 2)})


@website.post("/register_user")
async def register(request: Request, username: str = Form(...), password: str = Form(...)):
    created = await users.dependencies.create_user(password=password, username=username)
    print('qwe', 'created', created, 'username', username)
    # if not created:
    #     # TODO: render error message on the web page
    token, _ = await users.dependencies.create_token(username, password)
    # if token is None:
    #     TODO: render error message on the web page
    #     return RedirectResponse('/register', status_code=status.HTTP_302_FOUND)
    response = RedirectResponse('/exchange_keys', status_code=status.HTTP_302_FOUND)
    response.set_cookie(key='access_token', value=token)
    return response



@website.post("/update_exchange_keys")
async def register(request: Request, api_key: str = Form(...), api_secret: str = Form(...)):
    keys = users.schemas.ExchangeKeys.model_validate({"api_key": api_key, "api_secret": api_secret})

    access_token = request.cookies.get('access_token')

    try:
        user_id = await users.dependencies.validate_user(token=access_token)
        await users.router.update_keys(keys=keys, user=user_id)
        return RedirectResponse('/panel', status_code=status.HTTP_302_FOUND)
    except HTTPException:
        response = RedirectResponse('/exchange_keys', status_code=status.HTTP_302_FOUND)
        return response


@website.post("/add_exchange_keys")
async def add_exchange_keys(request: Request, api_key: str = Form(...), api_secret: str = Form(...)):
    keys = users.schemas.ExchangeKeys.model_validate({"api_key": api_key, "api_secret": api_secret})

    access_token = request.cookies.get('access_token')

    try:
        user = await users.dependencies.validate_user(token=access_token)
        await users.router.add_keys(keys=keys, user=user)
        return RedirectResponse('/panel', status_code=status.HTTP_302_FOUND)
    except HTTPException:
        response = RedirectResponse('/exchange_keys', status_code=status.HTTP_302_FOUND)
        return response


@website.get("/exchange_keys")
async def exchange_keys_page(request: Request):
    access_token = request.cookies.get('access_token')
    try:
        await users.dependencies.validate_user(token=access_token)
        return templates.TemplateResponse('exchange_keys.html', {'request': request})
    except HTTPException:
        return RedirectResponse('/login', status_code=status.HTTP_302_FOUND)


@website.get("/{symbol}")
async def open_trade_page(request: Request, symbol: str):
    try:
        keys = await get_exchange_keys(request)
        api_key = keys.api_key
        api_secret = keys.api_secret
        position = get_position_info(api_key=api_key, api_secret=api_secret, symbol=symbol)['result']['list']
        ticker = get_tickers(symbol=symbol, api_key=api_key, api_secret=api_secret)
    except HTTPException:
        response = RedirectResponse(f'/login', status_code=status.HTTP_302_FOUND)
        return response
    except FailedRequestError:
        response = RedirectResponse(f'/exchange_keys', status_code=status.HTTP_302_FOUND)
        return response
    except InvalidRequestError:
        response = RedirectResponse(f'/exchange_keys', status_code=status.HTTP_302_FOUND)
        return response

    return templates.TemplateResponse('pair.html',
                                      {'request': request, 'positions': position, 'ticker': ticker['result']['list'][0],
                                       'position': position[0]})
