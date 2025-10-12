import asyncio
from decimal import Decimal
from typing import Dict, List, Optional
import uuid
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor

from src.models.order import Order, OrderSide, OrderType
from src.models.trade import Trade
from .order_book import OrderBook

class MatchingEngine:
    def __init__(self):
        self.order_books: Dict[str, OrderBook] = {}
        self.trade_history: Dict[str, List[Trade]] = {}
        self.order_cache: Dict[str, Order] = {}
        self.processed_orders = 0
        self.start_time = datetime.utcnow()
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        self.logger = logging.getLogger("MatchingEngine")
    
    async def process_order(self, order: Order) -> List[Trade]:
        symbol = order.symbol
        
        if symbol not in self.order_books:
            self.order_books[symbol] = OrderBook(symbol)
            self.trade_history[symbol] = []
        
        order_book = self.order_books[symbol]
        self.order_cache[order.order_id] = order
        
        # Process order
        loop = asyncio.get_event_loop()
        trades = await loop.run_in_executor(
            self.thread_pool, 
            order_book.add_order, 
            order
        )
        
        for trade in trades:
            self.trade_history[symbol].append(trade)
        
        self.processed_orders += 1
        return trades
    
    def get_order_book_state(self, symbol: str, depth: int = 10) -> Optional[Dict]:
        if symbol not in self.order_books:
            return None
        
        order_book = self.order_books[symbol]
        bbo = order_book.get_bbo()
        depth_data = order_book.get_depth(depth)
        
        return {
            "symbol": symbol,
            "best_bid": str(bbo[0]) if bbo[0] else None,
            "best_ask": str(bbo[1]) if bbo[1] else None,
            "bids": depth_data["bids"],
            "asks": depth_data["asks"],
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def get_performance_stats(self) -> Dict:
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        return {
            "processed_orders": self.processed_orders,
            "uptime_seconds": uptime,
            "orders_per_second": self.processed_orders / uptime if uptime > 0 else 0,
            "active_symbols": len(self.order_books)
        }