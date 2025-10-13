import asyncio
import time
import psutil
import os
from decimal import Decimal
from datetime import datetime, timezone
import random

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.order import Order, OrderSide, OrderType
from src.engine.matching_engine import MatchingEngine

def get_memory_usage():
    """Get current memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024  # Convert to MB

async def memory_benchmark():
    """Benchmark memory usage under load"""
    print("🧠 Memory Usage Benchmark")
    print("="*40)
    
    initial_memory = get_memory_usage()
    print(f"Initial memory: {initial_memory:.2f} MB")
    
    engine = MatchingEngine()
    symbol = "BTC-USDT"
    
    # Track memory usage at different order counts
    memory_readings = []
    order_counts = [100, 500, 1000, 2000, 5000]
    
    for target_orders in order_counts:
        # Generate orders
        orders = []
        for i in range(100):  # Process in batches of 100
            side = OrderSide.BUY if random.random() > 0.5 else OrderSide.SELL
            price = Decimal('50000') + Decimal(str(random.randint(-500, 500)))
            quantity = Decimal(str(round(random.uniform(0.1, 10.0), 2)))
            
            order = Order(
                order_id=f"mem_{target_orders}_{i}",
                symbol=symbol,
                order_type=OrderType.LIMIT,
                side=side,
                quantity=quantity,
                price=price,
                timestamp=datetime.now(timezone.utc)
            )
            orders.append(order)
        
        # Process batch
        for order in orders:
            await engine.process_order(order)
        
        # Measure memory
        current_memory = get_memory_usage()
        memory_readings.append((target_orders, current_memory))
        
        print(f"After {target_orders:4d} orders: {current_memory:6.2f} MB "
              f"(Δ: {current_memory - initial_memory:+.2f} MB)")
    
    # Calculate memory per order
    if len(memory_readings) > 1:
        memory_per_order = (memory_readings[-1][1] - initial_memory) / memory_readings[-1][0]
        print(f"\n📏 Memory usage per order: {memory_per_order:.4f} MB/order")
    
    return memory_readings

if __name__ == "__main__":
    asyncio.run(memory_benchmark())