import asyncio
import time
from decimal import Decimal
from datetime import datetime,timezone
import random

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.order import Order, OrderSide, OrderType
from src.engine.matching_engine import MatchingEngine

async def quick_benchmark():
    """Quick performance test"""
    print("⚡ Quick Performance Benchmark")
    print("="*40)
    
    engine = MatchingEngine()
    symbol = "BTC-USDT"
    num_orders = 100
    
    # Generate test orders
    orders = []
    for i in range(num_orders):
        side = OrderSide.BUY if random.random() > 0.5 else OrderSide.SELL
        price = Decimal('50000') + Decimal(str(random.randint(-100, 100)))
        quantity = Decimal(str(round(random.uniform(0.1, 5.0), 2)))
        
        order = Order(
            order_id=f"quick_{i}",
            symbol=symbol,
            order_type=OrderType.LIMIT,
            side=side,
            quantity=quantity,
            price=price,
            timestamp=datetime.now(timezone.utc)
        )
        orders.append(order)
    
    # Benchmark
    start_time = time.time()
    
    processed = 0
    for order in orders:
        await engine.process_order(order)
        processed += 1
    
    end_time = time.time()
    
    # Results
    duration = end_time - start_time
    throughput = processed / duration
    
    print(f"📊 RESULTS:")
    print(f"   Orders Processed: {processed:,}")
    print(f"   Total Time: {duration:.3f} seconds")
    print(f"   Throughput: {throughput:,.1f} orders/second")
    print(f"   Avg Latency: {(duration/processed)*1000:.2f} ms/order")
    
    # Get final order book stats
    order_book = engine.get_order_book_state(symbol)
    if order_book:
        print(f"   Final BBO: {order_book['best_bid']} / {order_book['best_ask']}")
        print(f"   Bid Levels: {len(order_book['bids'])}")
        print(f"   Ask Levels: {len(order_book['asks'])}")
    
    stats = engine.get_performance_stats()
    print(f"   Engine Uptime: {stats['uptime_seconds']:.1f}s")
    print(f"   Total Orders: {stats['processed_orders']:,}")

if __name__ == "__main__":
    asyncio.run(quick_benchmark())