# fastApiMozart

An api and web interface for manage signals from Mozart Trade telegram channel

Work about project in progress
Python 3.10
## How to run
1. Clone the project
2. Install requirements.txt
```sh
pip install -r requirements.txt
```
3. Create and fill .env file
```
ALGORITHM_KEY=algorith_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRES=expired_range_time(1 = 1day
CRYPTOCOMPARE_API_KEY=key from cryptocompare(only for api)
MIDDLEWARE_KEY=middleware_key
```
For generating Algorithm key and Middleware key use command
```sh
openssl rand -hex 32
```
4. Run bot
```sh
uvicorn main:app --reload
```

## How to make signal for trade
![2023-12-21 16 39 04](https://github.com/originalmalek/mozart-trade/assets/56593369/29575dad-0cfa-4fa5-9363-bd36bd224301)

1. Go to the [google sheet](https://docs.google.com/spreadsheets/d/1natldn_OdGTObRMEMCLbTaAvGc6fpmKdpT16dAtBkkc/edit?usp=sharing)
2. Fill the columns
example:
```
Symbol: BTCUSDT
Side: Buy or Sell
Market_entry: 1 or 0
Stop Loss Type: ST or Fix
Stop Loss Price: 30000
Add orders: 31000,32000,33000
Position Quantity: your position amount for all orders(enter and add orders). The value ignores if Risk > 0
Take Profit Orders: 39000, 40000, 41000
Risk: 50. Risk ignores if value is 0, then uses Position Quantity
```  
Copy dictionary with trading data  
4. Send your dict with an endpoint /create_trade or in the webinterface


## How to manage
Use endpoints from docs of [fastapi](http://127.0.0.1:8000/docs) or use [web interface](http://127.0.0.1:8000/)

## Contacts
telegram @originalmalek

