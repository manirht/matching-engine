import asyncio
import time
from decimal import Decimal
from datetime import datetime,timezone
import random
import sys
import os

# Add project path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.order import Order, OrderSide, OrderType
from src.engine.matching_engine import MatchingEngine

# ✅ FIXED random seed for deterministic runs
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

async def run_benchmark(num_orders: int):
    """Run deterministic benchmark for a given number of orders"""
    engine = MatchingEngine()
    symbol = "BTC-USDT"
    base_price = Decimal('50000')

    print(f"\n🔹 Running benchmark for {num_orders:,} orders...")

    # Generate deterministic test orders
    orders = []
    for i in range(num_orders):
        side = OrderSide.BUY if random.random() > 0.5 else OrderSide.SELL
        price_offset = random.randint(-200, 200)
        price = base_price + Decimal(price_offset)
        quantity = Decimal(str(round(random.uniform(0.1, 5.0), 2)))

        order = Order(
            order_id=f"bench_{i}",
            symbol=symbol,
            order_type=OrderType.LIMIT,
            side=side,
            quantity=quantity,
            price=price,
            timestamp=datetime.now(timezone.utc)
        )
        orders.append(order)

    # Warm-up phase (stabilize GC, caches, etc.)
    warmup_orders = orders[:min(1000, num_orders)]
    for order in warmup_orders:
        await engine.process_order(order)

    # Benchmark phase
    start_time = time.perf_counter()
    processed_count = 0

    for order in orders:
        await engine.process_order(order)
        processed_count += 1

    end_time = time.perf_counter()
    duration = end_time - start_time
    throughput = processed_count / duration
    avg_latency_ms = (duration / processed_count) * 1000

    print(f"✅ Done: {processed_count:,} orders in {duration:.2f}s")
    print(f"➡ Throughput: {throughput:,.2f} orders/sec")
    print(f"➡ Avg Latency: {avg_latency_ms:.4f} ms/order")

    # Return metrics for later comparison
    return {
        "num_orders": num_orders,
        "duration": duration,
        "throughput": throughput,
        "avg_latency_ms": avg_latency_ms
    }

async def main():
    """Run deterministic benchmarks with multiple load levels"""
    print("=== Matching Engine Deterministic Benchmark ===")
    print(f"Random seed: {RANDOM_SEED}\n")

    # Different test scales
    order_counts = [1_000, 10_000, 50_000, 100_000,1_000_000]
    results = []

    for count in order_counts:
        result = await run_benchmark(count)
        results.append(result)

    # Print summary table
    print("\n=== 📊 Benchmark Summary ===")
    print(f"{'Orders':>10} | {'Time (s)':>9} | {'Throughput (ops/s)':>20} | {'Latency (ms)':>15}")
    print("-" * 65)
    for r in results:
        print(f"{r['num_orders']:>10,} | {r['duration']:>9.2f} | {r['throughput']:>20.2f} | {r['avg_latency_ms']:>15.4f}")

    print("\n✅ Benchmark completed with fixed random seed. Results are reproducible.")

if __name__ == "__main__":
    asyncio.run(main())
