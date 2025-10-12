from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from typing import Optional
import uuid

@dataclass
class Trade:
    symbol: str
    price: Decimal
    quantity: Decimal
    aggressor_side: str
    maker_order_id: str
    taker_order_id: str
    timestamp: datetime
    trade_id: Optional[str] = None
    
    def __post_init__(self):
        if self.trade_id is None:
            self.trade_id = str(uuid.uuid4())
    
    def to_dict(self):
        return {
            "trade_id": self.trade_id,
            "timestamp": self.timestamp.isoformat() + "Z",
            "symbol": self.symbol,
            "price": str(self.price),
            "quantity": str(self.quantity),
            "aggressor_side": self.aggressor_side,
            "maker_order_id": self.maker_order_id,
            "taker_order_id": self.taker_order_id
        }