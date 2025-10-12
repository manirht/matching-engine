import unittest
import asyncio
from decimal import Decimal
from datetime import datetime

from src.models.order import Order, OrderSide, OrderType
from src.engine.matching_engine import MatchingEngine

class TestMatchingEngine(unittest.TestCase):
    def setUp(self):
        self.engine = MatchingEngine()
        self.symbol = "BTC-USDT"
    
    def test_limit_order_matching(self):
        """Test basic limit order matching"""
        # Add buy order
        buy_order = Order(
            order_id="1",
            symbol=self.symbol,
            order_type=OrderType.LIMIT,
            side=OrderSide.BUY,
            quantity=Decimal('1.0'),
            price=Decimal('50000.0'),
            timestamp=datetime.utcnow()
        )
        
        # Add sell order that matches
        sell_order = Order(
            order_id="2", 
            symbol=self.symbol,
            order_type=OrderType.LIMIT,
            side=OrderSide.SELL,
            quantity=Decimal('1.0'),
            price=Decimal('50000.0'),
            timestamp=datetime.utcnow()
        )
        
        # Process buy order (should rest in book)
        trades1 = asyncio.run(self.engine.process_order(buy_order))
        self.assertEqual(len(trades1), 0)
        
        # Process sell order (should match)
        trades2 = asyncio.run(self.engine.process_order(sell_order))
        self.assertEqual(len(trades2), 1)
        self.assertEqual(trades2[0].quantity, Decimal('1.0'))
        self.assertEqual(trades2[0].price, Decimal('50000.0'))
    
    def test_market_order(self):
        """Test market order execution"""
        # First add a limit order to the book
        limit_order = Order(
            order_id="3",
            symbol=self.symbol,
            order_type=OrderType.LIMIT,
            side=OrderSide.SELL,
            quantity=Decimal('2.0'),
            price=Decimal('51000.0'),
            timestamp=datetime.utcnow()
        )
        
        # Then market order against it
        market_order = Order(
            order_id="4",
            symbol=self.symbol,
            order_type=OrderType.MARKET,
            side=OrderSide.BUY,
            quantity=Decimal('1.5'),
            price=None,
            timestamp=datetime.utcnow()
        )
        
        asyncio.run(self.engine.process_order(limit_order))
        trades = asyncio.run(self.engine.process_order(market_order))
        
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0].price, Decimal('51000.0'))

if __name__ == '__main__':
    unittest.main()