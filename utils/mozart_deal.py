from pybit.exceptions import InvalidRequestError
from utils import bybit_api


def place_position_orders(one_order_position_amount, symbol, market_entry, side, add_orders, api_key, api_secret):
    if market_entry:
        bybit_api.open_order(symbol=symbol,
                             side=side,
                             quantity=one_order_position_amount,
                             api_key=api_key,
                             api_secret=api_secret,
                             order_type='Market',
                             price=0)

    for add_order_price in add_orders:
        bybit_api.open_order(symbol=symbol,
                             side=side,
                             quantity=one_order_position_amount,
                             order_type='Limit',
                             price=add_order_price,
                             api_key=api_key,
                             api_secret=api_secret)


def place_take_profit_orders(take_profit_order_amount, symbol, take_profit_orders, api_key, api_secret):
    for take_profit_order in take_profit_orders:
        bybit_api.trading_tp(symbol=symbol,
                             tp_size=take_profit_order_amount,
                             tp_price=take_profit_order,
                             api_key=api_key,
                             api_secret=api_secret)


def calculate_total_positions_amount(risk, stop_loss_price, position_amount, last_price):
    if risk:
        return risk / abs(last_price - stop_loss_price)
    else:
        return position_amount / last_price


def calculate_orders_quantity(market_entry, add_orders):
    if market_entry:
        return len(add_orders) + 1
    else:
        return len(add_orders)


def calculate_take_profit_order_amount(total_positions_amount, orders_quantity, num_decimal_digits,
                                       min_order_amount, take_profit_orders):
    one_order_position_amount = round((total_positions_amount / orders_quantity), num_decimal_digits)

    if one_order_position_amount < min_order_amount:
        one_order_position_amount = min_order_amount

    take_profit_order_amount = round(one_order_position_amount / len(take_profit_orders), num_decimal_digits)
    return take_profit_order_amount


def get_num_decimal_digits(min_order_amount):
    # Возвращает возможное макс количество знаков после запятой в ордере
    decimal_part = str(min_order_amount).split('.')[1]
    num_decimal_digits = len(decimal_part)

    if num_decimal_digits == 1 and decimal_part == '0':
        num_decimal_digits = 0

    return num_decimal_digits


def get_last_price(symbol, api_key, api_secret):
    ticker = bybit_api.get_tickers(symbol=symbol,
                                   api_key=api_key,
                                   api_secret=api_secret)
    return float(ticker['result']['list'][0]['lastPrice'])


def get_minimum_order_amount(symbol, api_key, api_secret):
    instrument_info = bybit_api.get_instruments_info(symbol=symbol,api_key=api_key,api_secret=api_secret)
    return float(instrument_info['result']['list'][0]['lotSizeFilter']['minOrderQty'])


# noinspection PyArgumentList
def place_orders(trade, api_key, api_secret):
    symbol = trade['symbol'].upper()
    side = trade['side']
    market_entry = trade['market_entry']
    stop_loss_type = trade['stop_loss_type']
    stop_loss_price = trade['stop_loss_price']
    add_orders = trade['add_orders']
    position_amount = trade['position_amount']
    take_profit_orders = trade['take_profit_orders']
    risk = trade['risk']

    min_order_amount = get_minimum_order_amount(symbol, api_key, api_secret)
    last_price = get_last_price(symbol, api_key, api_secret)
    num_decimal_digits = get_num_decimal_digits(min_order_amount)
    total_positions_amount = calculate_total_positions_amount(risk,
                                                              stop_loss_price,
                                                              position_amount,
                                                              last_price)
    orders_quantity = calculate_orders_quantity(market_entry,
                                                add_orders)

    take_profit_order_amount = calculate_take_profit_order_amount(total_positions_amount,
                                                                  orders_quantity,
                                                                  num_decimal_digits,
                                                                  min_order_amount,
                                                                  take_profit_orders)

    one_order_position_amount = round(take_profit_order_amount * len(take_profit_orders), num_decimal_digits)

    place_position_orders(one_order_position_amount,
                          symbol,
                          market_entry,
                          side,
                          add_orders, api_key, api_secret)

    place_take_profit_orders(take_profit_order_amount,
                             symbol,
                             take_profit_orders,
                             api_key, api_secret)

    if stop_loss_type == 'Fix':
        bybit_api.trading_stop(symbol=symbol,
                               sl_size=total_positions_amount,
                               sl_price=stop_loss_price,
                               api_key=api_key,
                               api_secret=api_secret)


def set_leverage(symbol: str, api_key: str, api_secret: str):
    try:
        bybit_api.switch_margin_mode(symbol=symbol,
                                     api_key=api_key,
                                     api_secret=api_secret)
    except InvalidRequestError:
        print(f'Isolated mode already set {symbol}')

    try:
        bybit_api.set_leverage(symbol=symbol,
                               api_key=api_key,
                               api_secret=api_secret)
    except InvalidRequestError:
        print(f'Leverage already set {symbol}')


def create_trade(trade, api_key, api_secret):
    try:
        set_leverage(trade['symbol'], api_key, api_secret)
        place_orders(trade, api_key, api_secret)
        return True
    except Exception as e:
        return str(e)


def cancel_trade(symbol, api_key, api_secret):
    symbol = symbol.upper()
    try:
        open_trade = bybit_api.get_position_info(symbol=symbol,
                                                 api_key=api_key,
                                                 api_secret=api_secret)
        if open_trade['result']['list'][0]['side'] == 'None':
            return False
        trade_side = open_trade['result']['list'][0]['side']
        trade_amount = open_trade['result']['list'][0]['size']

        bybit_api.open_order(symbol=symbol,
                             side='Sell' if trade_side == 'Buy' else 'Buy',
                             quantity=trade_amount,
                             order_type='Market',
                             price=None,
                             api_key=api_key,
                             api_secret=api_secret)

        bybit_api.cancel_all_orders(symbol=symbol,
                                    api_key=api_key,
                                    api_secret=api_secret)
        return True
    except InvalidRequestError as e:
        return str(e)


def cancel_add_orders(symbol, api_key, api_secret):
    symbol = symbol.upper()
    try:
        open_trade = bybit_api.get_position_info(symbol=symbol,
                                                 api_key=api_key,
                                                 api_secret=api_secret)

        if open_trade['result']['list'][0]['side'] == 'None':
            return False

        trade_side = open_trade['result']['list'][0]['side']

        open_orders = bybit_api.get_open_orders(symbol=symbol, api_key=api_key, api_secret=api_secret)

        for open_order in open_orders['result']['list']:
            if trade_side == open_order['side']:
                bybit_api.cancel_order(symbol=symbol,
                                       order_id=open_order['orderId'],
                                       api_secret=api_secret,
                                       api_key=api_key)

        return True

    except InvalidRequestError as e:
        return str(e)


def set_sl_breakeven(symbol, api_key, api_secret):
    symbol = symbol.upper()
    try:
        open_trade = bybit_api.get_position_info(symbol=symbol,
                                                 api_key=api_key,
                                                 api_secret=api_secret)

        if open_trade['result']['list'][0]['side'] == 'None':
            return False
        trade_avg_price = open_trade['result']['list'][0]['avgPrice']
        trade_amount = open_trade['result']['list'][0]['size']
        bybit_api.trading_stop(symbol=symbol,
                               sl_size=trade_amount,
                               sl_price=trade_avg_price,
                               api_key=api_key,
                               api_secret=api_secret)
        return True
    except InvalidRequestError as e:
        return str(e)
