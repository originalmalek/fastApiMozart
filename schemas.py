from pydantic import BaseModel, Extra
from typing import Literal, List, Union



class Signal(BaseModel, extra=Extra.forbid):
    symbol: str
    side: Literal['Buy', 'Sell']
    market_entry: Literal[0, 1]
    stop_loss_type: Literal['ST', 'Fix']
    stop_loss_price: float
    add_orders: List[float]
    risk: float
    position_amount: float
    take_profit_orders: List[float]

class Symbol(BaseModel):
    symbol: str


class CoinsData(BaseModel):
    coins_from: Union[List[str], str]
    coins_to: Union[List[str], str]
