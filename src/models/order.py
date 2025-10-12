from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Optional
import uuid
from datetime import datetime

class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    IOC = "ioc"
    FOK = "fok"

@dataclass
class Order:
    order_id: str
    symbol: str
    order_type: OrderType
    side: OrderSide
    quantity: Decimal
    price: Optional[Decimal]
    timestamp: datetime
    user_id: Optional[str] = None
    
    def __post_init__(self):
        if self.order_type == OrderType.LIMIT and self.price is None:
            raise ValueError("Limit orders must have a price")
        if self.quantity <= Decimal('0'):
            raise ValueError("Quantity must be positive")