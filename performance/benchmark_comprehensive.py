import asyncio
import time
import statistics
from decimal import Decimal
from datetime import datetime, timezone
import random
import json
import sys
import os
from typing import List, Dict

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.order import Order, OrderSide, OrderType
from src.engine.matching_engine import MatchingEngine

try:
    import matplotlib.pyplot as plt
    import numpy as np
    PLOTS_AVAILABLE = True
except ImportError:
    PLOTS_AVAILABLE = False

class ComprehensiveBenchmark:
    def __init__(self):
        self.results = {}
        self.latency_measurements = []
        
    async def benchmark_throughput(self, num_orders: int = 1000) -> Dict:
        """Benchmark order processing throughput"""
        print(f"🚀 Starting throughput benchmark with {num_orders} orders...")
        
        engine = MatchingEngine()
        symbol = "BTC-USDT"
        
        # Generate test orders
        orders = self._generate_orders(num_orders, symbol)
        
        # Warm-up phase (process first 100 orders)
        print("🔥 Warm-up phase...")
        for order in orders[:100]:
            await engine.process_order(order)
        
        # Actual benchmark
        print("⏱️  Starting benchmark...")
        start_time = time.time()
        
        processed_count = 0
        for i, order in enumerate(orders[100:], 1):
            order_start = time.time()
            trades = await engine.process_order(order)
            order_end = time.time()
            
            # Record latency
            self.latency_measurements.append((order_end - order_start) * 1000)  # Convert to ms
            processed_count += 1
            
            if processed_count % 200 == 0:
                print(f"   Processed {processed_count}/{num_orders-100} orders...")
        
        end_time = time.time()
        
        # Calculate metrics
        total_time = end_time - start_time
        
        if self.latency_measurements:
            avg_latency = statistics.mean(self.latency_measurements)
            throughput = processed_count / total_time
        else:
            avg_latency = 0
            throughput = 0
        
        self.results['throughput'] = {
            'total_orders': processed_count,
            'total_time_seconds': total_time,
            'throughput_ops': throughput,
            'average_latency_ms': avg_latency,
            'min_latency_ms': min(self.latency_measurements) if self.latency_measurements else 0,
            'max_latency_ms': max(self.latency_measurements) if self.latency_measurements else 0
        }
        
        # Calculate percentiles if we have measurements
        if self.latency_measurements:
            if PLOTS_AVAILABLE:
                self.results['throughput']['p95_latency_ms'] = np.percentile(self.latency_measurements, 95)
                self.results['throughput']['p99_latency_ms'] = np.percentile(self.latency_measurements, 99)
            else:
                # Simple percentile calculation without numpy
                sorted_latencies = sorted(self.latency_measurements)
                self.results['throughput']['p95_latency_ms'] = sorted_latencies[int(0.95 * len(sorted_latencies))]
                self.results['throughput']['p99_latency_ms'] = sorted_latencies[int(0.99 * len(sorted_latencies))]
        
        return self.results['throughput']
    
    async def benchmark_order_types(self, orders_per_type: int = 300) -> Dict:
        """Benchmark different order types - FIXED VERSION"""
        print(f"\n📊 Benchmarking order types ({orders_per_type} orders per type)...")
        
        engine = MatchingEngine()
        symbol = "BTC-USDT"
        
        order_type_results = {}
        
        # Test each order type
        for order_type in [OrderType.LIMIT, OrderType.MARKET, OrderType.IOC, OrderType.FOK]:
            print(f"   Testing {order_type.value} orders...")
            
            # Pre-populate book for meaningful tests
            await self._prepopulate_order_book(engine, symbol)
            
            latencies = []
            processed_count = 0
            start_time = time.time()
            
            for i in range(orders_per_type):
                try:
                    order = self._generate_specific_order(symbol, order_type, i)
                    order_start = time.time()
                    trades = await engine.process_order(order)
                    order_end = time.time()
                    latencies.append((order_end - order_start) * 1000)
                    processed_count += 1
                except Exception as e:
                    print(f"      Error processing {order_type.value} order {i}: {e}")
                    continue
            
            end_time = time.time()
            total_time = end_time - start_time
            
            if processed_count > 0:
                order_type_results[order_type.value] = {
                    'processed_orders': processed_count,
                    'throughput_ops': processed_count / total_time,
                    'average_latency_ms': statistics.mean(latencies) if latencies else 0
                }
            else:
                order_type_results[order_type.value] = {
                    'processed_orders': 0,
                    'throughput_ops': 0,
                    'average_latency_ms': 0
                }
        
        self.results['order_types'] = order_type_results
        return order_type_results
    
    async def benchmark_concurrent_orders(self, total_orders: int = 1000, concurrency: int = 10) -> Dict:
        """Benchmark concurrent order processing"""
        print(f"\n⚡ Benchmarking concurrent orders ({total_orders} orders, {concurrency} concurrent)...")
        
        engine = MatchingEngine()
        symbol = "BTC-USDT"
        
        # Generate orders
        orders = self._generate_orders(total_orders, symbol)
        
        # Pre-populate book
        await self._prepopulate_order_book(engine, symbol)
        
        semaphore = asyncio.Semaphore(concurrency)
        latencies = []
        processed_count = 0
        
        async def process_with_semaphore(order):
            nonlocal processed_count
            async with semaphore:
                try:
                    order_start = time.time()
                    await engine.process_order(order)
                    order_end = time.time()
                    latencies.append((order_end - order_start) * 1000)
                    processed_count += 1
                except Exception as e:
                    print(f"   Error in concurrent processing: {e}")
        
        start_time = time.time()
        
        # Process orders concurrently
        tasks = [process_with_semaphore(order) for order in orders]
        await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        concurrent_results = {
            'total_orders': total_orders,
            'processed_orders': processed_count,
            'concurrency_level': concurrency,
            'total_time_seconds': total_time,
            'throughput_ops': processed_count / total_time if total_time > 0 else 0,
            'average_latency_ms': statistics.mean(latencies) if latencies else 0
        }
        
        self.results['concurrent'] = concurrent_results
        return concurrent_results
    
    async def benchmark_scalability(self, max_orders: int = 2000, step: int = 400) -> Dict:
        """Benchmark how performance scales with order volume"""
        print(f"\n📈 Benchmarking scalability (up to {max_orders} orders)...")
        
        scalability_results = {}
        
        for num_orders in range(step, max_orders + 1, step):
            print(f"   Testing with {num_orders} orders...")
            
            engine = MatchingEngine()
            symbol = "BTC-USDT"
            orders = self._generate_orders(num_orders, symbol)
            
            start_time = time.time()
            
            processed_count = 0
            for order in orders:
                try:
                    await engine.process_order(order)
                    processed_count += 1
                except Exception as e:
                    print(f"      Error processing order: {e}")
                    continue
            
            end_time = time.time()
            total_time = end_time - start_time
            
            scalability_results[num_orders] = {
                'processed_orders': processed_count,
                'throughput_ops': processed_count / total_time if total_time > 0 else 0,
                'total_time_seconds': total_time,
                'orders_per_second': processed_count / total_time if total_time > 0 else 0
            }
        
        self.results['scalability'] = scalability_results
        return scalability_results
    
    def _generate_orders(self, num_orders: int, symbol: str) -> List[Order]:
        """Generate realistic test orders - FIXED VERSION"""
        orders = []
        base_price = Decimal('50000')
        
        for i in range(num_orders):
            # Vary sides randomly
            side = OrderSide.BUY if random.random() > 0.5 else OrderSide.SELL
            
            # Create realistic price distribution (clustered around base price)
            price_offset = random.randint(-500, 500)
            price = base_price + Decimal(str(price_offset))
            
            # Vary quantities realistically
            quantity = Decimal(str(round(random.uniform(0.1, 10.0), 2)))
            
            # Mix of order types (80% limit, 10% market, 5% IOC, 5% FOK)
            rand_type = random.random()
            if rand_type < 0.8:
                order_type = OrderType.LIMIT
                # Keep the price for limit orders
                current_price = price
            elif rand_type < 0.9:
                order_type = OrderType.MARKET
                current_price = None  # Market orders don't have prices
            elif rand_type < 0.95:
                order_type = OrderType.IOC
                current_price = price  # IOC orders DO have prices!
            else:
                order_type = OrderType.FOK
                current_price = price  # FOK orders DO have prices!
            
            order = Order(
                order_id=f"bench_{i}_{int(time.time()*1000)}",
                symbol=symbol,
                order_type=order_type,
                side=side,
                quantity=quantity,
                price=current_price,  # Use the appropriately set price
                timestamp=datetime.now(timezone.utc)
            )
            orders.append(order)
        
        return orders
    
    def _generate_specific_order(self, symbol: str, order_type: OrderType, index: int) -> Order:
        """Generate a specific type of order - FIXED VERSION"""
        base_price = Decimal('50000')
        price_offset = random.randint(-200, 200)
        
        side = OrderSide.BUY if index % 2 == 0 else OrderSide.SELL
        
        # FIX: IOC and FOK orders MUST have prices, only MARKET orders don't
        if order_type == OrderType.MARKET:
            price = None
        else:
            price = base_price + Decimal(str(price_offset))
            
        quantity = Decimal(str(round(random.uniform(0.1, 5.0), 2)))
        
        return Order(
            order_id=f"{order_type.value}_{index}_{int(time.time()*1000)}",
            symbol=symbol,
            order_type=order_type,
            side=side,
            quantity=quantity,
            price=price,
            timestamp=datetime.now(timezone.utc)
        )
    
    async def _prepopulate_order_book(self, engine: MatchingEngine, symbol: str, num_levels: int = 20):
        """Pre-populate order book with some resting orders"""
        base_price = Decimal('50000')
        
        # Add some initial bids
        for i in range(num_levels):
            bid_price = base_price - Decimal(str(i * 10))
            bid_order = Order(
                order_id=f"init_bid_{i}",
                symbol=symbol,
                order_type=OrderType.LIMIT,
                side=OrderSide.BUY,
                quantity=Decimal('5.0'),
                price=bid_price,
                timestamp=datetime.now(timezone.utc)
            )
            await engine.process_order(bid_order)
        
        # Add some initial asks
        for i in range(num_levels):
            ask_price = base_price + Decimal(str(i * 10))
            ask_order = Order(
                order_id=f"init_ask_{i}",
                symbol=symbol,
                order_type=OrderType.LIMIT,
                side=OrderSide.SELL,
                quantity=Decimal('5.0'),
                price=ask_price,
                timestamp=datetime.now(timezone.utc)
            )
            await engine.process_order(ask_order)
    
    def generate_report(self):
        """Generate a comprehensive benchmark report"""
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE BENCHMARK REPORT")
        print("="*80)
        
        if 'throughput' in self.results:
            t = self.results['throughput']
            print(f"\n🎯 THROUGHPUT & LATENCY ({t['total_orders']:,} orders):")
            print(f"   Throughput: {t['throughput_ops']:,.2f} orders/second")
            print(f"   Total Time: {t['total_time_seconds']:.2f} seconds")
            print(f"   Average Latency: {t['average_latency_ms']:.2f} ms")
            if 'p95_latency_ms' in t:
                print(f"   P95 Latency: {t['p95_latency_ms']:.2f} ms")
                print(f"   P99 Latency: {t['p99_latency_ms']:.2f} ms")
            print(f"   Min Latency: {t['min_latency_ms']:.2f} ms")
            print(f"   Max Latency: {t['max_latency_ms']:.2f} ms")
        
        if 'order_types' in self.results:
            print(f"\n📋 ORDER TYPE PERFORMANCE:")
            for order_type, metrics in self.results['order_types'].items():
                print(f"   {order_type.upper():<6}: {metrics['processed_orders']:3} orders, "
                      f"{metrics['throughput_ops']:6.1f} ops/sec, "
                      f"avg latency: {metrics['average_latency_ms']:5.2f} ms")
        
        if 'concurrent' in self.results:
            c = self.results['concurrent']
            print(f"\n⚡ CONCURRENT PROCESSING (concurrency: {c['concurrency_level']}):")
            print(f"   Processed: {c['processed_orders']}/{c['total_orders']} orders")
            print(f"   Throughput: {c['throughput_ops']:,.2f} orders/second")
            print(f"   Average Latency: {c['average_latency_ms']:.2f} ms")
        
        if 'scalability' in self.results:
            print(f"\n📈 SCALABILITY ANALYSIS:")
            orders = list(self.results['scalability'].keys())
            throughputs = [self.results['scalability'][o]['throughput_ops'] for o in orders]
            
            if throughputs:
                print(f"   Orders Range: {min(orders):,} - {max(orders):,}")
                print(f"   Throughput Range: {min(throughputs):.1f} - {max(throughputs):.1f} ops/sec")
                print(f"   Average Throughput: {statistics.mean(throughputs):.1f} ops/sec")
        
        # Save results to file
        self._save_results_to_file()
    
    def _save_results_to_file(self):
        """Save benchmark results to JSON file"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_results_{timestamp}.json"
        
        # Convert Decimal to float for JSON serialization
        def convert_decimals(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: convert_decimals(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_decimals(v) for v in obj]
            return obj
        
        results_serializable = convert_decimals(self.results)
        
        with open(filename, 'w') as f:
            json.dump(results_serializable, f, indent=2)
        
        print(f"\n💾 Results saved to: {filename}")
    
    def plot_results(self):
        """Generate plots for visualization (optional)"""
        if not PLOTS_AVAILABLE:
            print("📊 matplotlib not available - skipping plots")
            return
            
        try:
            if 'scalability' in self.results:
                orders = list(self.results['scalability'].keys())
                throughputs = [self.results['scalability'][o]['throughput_ops'] for o in orders]
                
                plt.figure(figsize=(10, 6))
                plt.plot(orders, throughputs, 'b-o', linewidth=2, markersize=6)
                plt.title('Matching Engine Scalability')
                plt.xlabel('Number of Orders')
                plt.ylabel('Throughput (orders/second)')
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                plt.savefig('scalability_plot.png', dpi=300, bbox_inches='tight')
                print("📊 Scalability plot saved as 'scalability_plot.png'")
            
            if 'throughput' in self.results and self.latency_measurements:
                plt.figure(figsize=(10, 6))
                plt.hist(self.latency_measurements, bins=50, alpha=0.7, edgecolor='black')
                plt.title('Order Processing Latency Distribution')
                plt.xlabel('Latency (milliseconds)')
                plt.ylabel('Frequency')
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                plt.savefig('latency_distribution.png', dpi=300, bbox_inches='tight')
                print("📊 Latency distribution plot saved as 'latency_distribution.png'")
                
        except Exception as e:
            print(f"📊 Plot generation failed: {e}")

async def run_complete_benchmark():
    """Run the complete benchmark suite"""
    benchmark = ComprehensiveBenchmark()
    
    print("🏁 STARTING COMPREHENSIVE BENCHMARK SUITE")
    print("="*60)
    
    # Run individual benchmarks
    await benchmark.benchmark_throughput(1000)  # Reduced from 2000 for stability
    await benchmark.benchmark_order_types(200)  # Reduced from 300
    await benchmark.benchmark_concurrent_orders(500, 5)  # Reduced from 1000
    await benchmark.benchmark_scalability(1000, 200)  # Reduced from 2000
    
    # Generate report
    benchmark.generate_report()
    
    # Generate plots
    benchmark.plot_results()
    
    return benchmark.results

if __name__ == "__main__":
    # Run benchmark
    print("🔧 Running comprehensive benchmark...")
    results = asyncio.run(run_complete_benchmark())
    
    print("\n✅ Benchmark completed!")  