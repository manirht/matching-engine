import heapq
from collections import deque
from decimal import Decimal
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import logging

from src.models.order import Order, OrderSide, OrderType
from src.models.trade import Trade

class PriceLevel:
    def __init__(self, price: Decimal):
        self.price = price
        self.orders = deque()
        self.total_quantity = Decimal('0')
    
    def add_order(self, order: Order):
        self.orders.append(order)
        self.total_quantity += order.quantity
    
    def remove_front_order(self) -> Optional[Order]:
        """Remove and return the front order from the price level"""
        if not self.orders:
            return None
        order = self.orders.popleft()
        self.total_quantity -= order.quantity
        return order

class OrderBook:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.bids: Dict[Decimal, PriceLevel] = {}
        self.asks: Dict[Decimal, PriceLevel] = {}
        self.bid_prices = []  # Max-heap (we store negative prices)
        self.ask_prices = []  # Min-heap
        self.best_bid = None
        self.best_ask = None
        self.logger = logging.getLogger(f"OrderBook_{symbol}")
    
    def add_order(self, order: Order) -> List[Trade]:
        trades = []
        
        if order.side == OrderSide.BUY:
            trades = self._match_buy_order(order)
        else:
            trades = self._match_sell_order(order)
            
        self._update_bbo()
        return trades
    
    def _match_buy_order(self, order: Order) -> List[Trade]:
        trades = []
        remaining_quantity = order.quantity
        
        # Check for IOC/FOK immediate fill capability
        if order.order_type in [OrderType.IOC, OrderType.FOK]:
            if not self._can_fill_immediately(order):
                return []
        
        # Match against existing asks
        while (remaining_quantity > Decimal('0') and self.ask_prices and 
               (order.order_type == OrderType.MARKET or 
                (order.price and order.price >= self.ask_prices[0]))):
            
            best_ask_price = self.ask_prices[0]
            ask_level = self.asks[best_ask_price]
            
            while ask_level.orders and remaining_quantity > Decimal('0'):
                resting_order = ask_level.orders[0]
                trade_quantity = min(remaining_quantity, resting_order.quantity)
                
                # Create trade
                trade = Trade(
                    symbol=self.symbol,
                    price=resting_order.price,
                    quantity=trade_quantity,
                    aggressor_side=order.side.value,
                    maker_order_id=resting_order.order_id,
                    taker_order_id=order.order_id,
                    timestamp=datetime.utcnow()
                )
                trades.append(trade)
                
                # Update quantities
                remaining_quantity -= trade_quantity
                resting_order.quantity -= trade_quantity
                ask_level.total_quantity -= trade_quantity
                
                # Remove fully filled resting order
                if resting_order.quantity == Decimal('0'):
                    ask_level.remove_front_order()
                
                # Remove empty price level
                if not ask_level.orders:
                    self._remove_price_level(OrderSide.SELL, best_ask_price)
                    break
            
            if not self.ask_prices:
                break
        
        # Handle remaining quantity
        if remaining_quantity > Decimal('0'):
            if order.order_type == OrderType.LIMIT:
                self._add_resting_order(order, remaining_quantity)
            # For IOC, FOK, MARKET - remaining quantity is cancelled
        
        return trades
    
    def _match_sell_order(self, order: Order) -> List[Trade]:
        trades = []
        remaining_quantity = order.quantity
        
        # Check for IOC/FOK immediate fill capability
        if order.order_type in [OrderType.IOC, OrderType.FOK]:
            if not self._can_fill_immediately(order):
                return []
        
        # Match against existing bids
        while (remaining_quantity > Decimal('0') and self.bid_prices and 
               (order.order_type == OrderType.MARKET or 
                (order.price and order.price <= -self.bid_prices[0]))):
            
            best_bid_price = -self.bid_prices[0]  # Convert back from max-heap
            bid_level = self.bids[best_bid_price]
            
            while bid_level.orders and remaining_quantity > Decimal('0'):
                resting_order = bid_level.orders[0]
                trade_quantity = min(remaining_quantity, resting_order.quantity)
                
                trade = Trade(
                    symbol=self.symbol,
                    price=resting_order.price,
                    quantity=trade_quantity,
                    aggressor_side=order.side.value,
                    maker_order_id=resting_order.order_id,
                    taker_order_id=order.order_id,
                    timestamp=datetime.utcnow()
                )
                trades.append(trade)
                
                remaining_quantity -= trade_quantity
                resting_order.quantity -= trade_quantity
                bid_level.total_quantity -= trade_quantity
                
                if resting_order.quantity == Decimal('0'):
                    bid_level.remove_front_order()
                
                if not bid_level.orders:
                    self._remove_price_level(OrderSide.BUY, best_bid_price)
                    break
            
            if not self.bid_prices:
                break
        
        if remaining_quantity > Decimal('0'):
            if order.order_type == OrderType.LIMIT:
                self._add_resting_order(order, remaining_quantity)
        
        return trades
    
    def _add_resting_order(self, order: Order, quantity: Decimal):
        """Add a resting order to the book"""
        order.quantity = quantity
        
        if order.side == OrderSide.BUY:
            if order.price not in self.bids:
                self.bids[order.price] = PriceLevel(order.price)
                # Use negative prices for max-heap
                heapq.heappush(self.bid_prices, -order.price)
            self.bids[order.price].add_order(order)
        else:  # SELL
            if order.price not in self.asks:
                self.asks[order.price] = PriceLevel(order.price)
                heapq.heappush(self.ask_prices, order.price)
            self.asks[order.price].add_order(order)
    
    def _remove_price_level(self, side: OrderSide, price: Decimal):
        """Remove a price level from the book"""
        if side == OrderSide.BUY:
            if price in self.bids:
                del self.bids[price]
                # Remove from heap (using negative price for max-heap)
                if -price in self.bid_prices:
                    self.bid_prices.remove(-price)
                    heapq.heapify(self.bid_prices)
        else:  # SELL
            if price in self.asks:
                del self.asks[price]
                if price in self.ask_prices:
                    self.ask_prices.remove(price)
                    heapq.heapify(self.ask_prices)
    
    def _can_fill_immediately(self, order: Order) -> bool:
        """Check if an IOC/FOK order can be filled immediately"""
        if order.side == OrderSide.BUY:
            if not self.ask_prices:
                return False
            if order.order_type == OrderType.MARKET:
                return True
            return order.price >= self.ask_prices[0]
        else:  # SELL
            if not self.bid_prices:
                return False
            if order.order_type == OrderType.MARKET:
                return True
            # For bids, we need to convert from max-heap storage
            return order.price <= -self.bid_prices[0]
    
    def _update_bbo(self):
        """Update Best Bid/Offer"""
        self.best_bid = -self.bid_prices[0] if self.bid_prices else None
        self.best_ask = self.ask_prices[0] if self.ask_prices else None
    
    def get_bbo(self) -> Tuple[Optional[Decimal], Optional[Decimal]]:
        """Get current Best Bid and Offer"""
        return self.best_bid, self.best_ask
    
    def get_depth(self, levels: int = 10) -> Dict:
        """Get order book depth"""
        # For bids: we have negative prices in the heap, so convert back
        bid_prices_sorted = sorted([(-p, self.bids[-p]) for p in self.bid_prices], 
                                 key=lambda x: x[0], reverse=True)[:levels]
        ask_prices_sorted = sorted([(p, self.asks[p]) for p in self.ask_prices], 
                                 key=lambda x: x[0])[:levels]
        
        return {
            "bids": [[str(price), str(level.total_quantity)] for price, level in bid_prices_sorted],
            "asks": [[str(price), str(level.total_quantity)] for price, level in ask_prices_sorted]
        }