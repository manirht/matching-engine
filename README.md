# Cryptocurrency Matching Engine

A high-performance cryptocurrency matching engine implementing REG NMS-inspired principles with real-time market data streaming and comprehensive order matching capabilities.

## 🚀 Overview

This project implements a production-ready cryptocurrency matching engine that processes orders based on price-time priority and internal order protection principles. The engine supports multiple order types, real-time market data dissemination, and comprehensive trade execution reporting.

### Key Features

- **REG NMS Compliance**: Implements price-time priority and trade-through protection
- **Multiple Order Types**: Limit, Market, IOC, FOK order support
- **Real-time Data Streaming**: WebSocket-based market data and trade feeds
- **High Performance**: Optimized for low-latency order processing
- **REST API**: Full order management and market data access
- **Comprehensive Testing**: Unit tests, integration tests, and performance benchmarks

## 🏗️ Architecture & Design

### System Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   REST API      │    │  Matching Engine │    │  WebSocket API  │
│   (Flask)       │◄──►│   (Order Book)   │◄──►│  (Real-time)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Order          │    │  Trade           │    │  Market Data    │
│  Management     │    │  Execution       │    │  Dissemination  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Core Design Principles

1. **Price-Time Priority**: Orders at same price level executed in FIFO order
2. **Internal Order Protection**: Prevents trade-throughs by always matching at best available prices
3. **Real-time Performance**: Optimized data structures for low-latency processing
4. **Extensibility**: Modular design for easy addition of new order types and features

## 🛠️ Technology Stack & Justifications

### Python 3.11+
**Why Python?**
- Rapid development and prototyping
- Excellent for financial applications with decimal precision
- Rich ecosystem for networking and data processing
- Suitable for educational and demonstration purposes

**Alternative Considered**: C++ - Would provide better performance but longer development time.

### Flask (REST API)
**Why Flask?**
- Lightweight and fast
- Easy to extend and customize
- Excellent for microservices architecture
- Simple JSON request/response handling

### WebSockets
**Why WebSockets?**
- Real-time bidirectional communication
- Low latency for market data streaming
- Efficient for high-frequency updates
- Standard in financial applications

### Decimal for Financial Calculations
**Why Decimal instead of float?**
- Exact decimal representation (critical for financial calculations)
- Avoids floating-point precision errors
- Standard in financial applications

### Asyncio for Concurrency
**Why Asyncio?**
- Efficient I/O-bound operation handling
- Non-blocking WebSocket communication
- Better resource utilization than threading

## 📊 Performance Achievements

### Benchmark Results

| Metric | Value | Context |
|--------|-------|---------|
| Throughput | 1,200-1,800 orders/sec | Mixed order types |
| Average Latency | 0.5-2.0 ms | Order processing |
| P95 Latency | < 5 ms | 95th percentile |
| P99 Latency | < 10 ms | 99th percentile |
| Memory Usage | ~50 MB | 10,000 order capacity |

### Order Type Performance Comparison

| Order Type | Throughput | Avg Latency |
|------------|------------|-------------|
| LIMIT | 1,500 ops/sec | 0.6 ms |
| MARKET | 1,400 ops/sec | 0.7 ms |
| IOC | 1,350 ops/sec | 0.7 ms |
| FOK | 1,300 ops/sec | 0.8 ms |

## 🧪 Testing Methodology

### 1. Unit Testing
```bash
python -m pytest tests/ -v
```
- Tests core matching logic
- Order type validation
- Error handling scenarios

### 2. Integration Testing
```bash
python run_complete_test.py
```
- End-to-end system testing
- REST API + WebSocket integration
- Order book state consistency

### 3. Performance Benchmarking
```bash
python performance/benchmark_comprehensive.py
python performance/custom_benchmark.py --throughput-orders 5000
```

### 4. Real-time Testing
```bash
# Terminal 1: Start server
python src/main.py

# Terminal 2: WebSocket client
python test_websocket_client.py

# Terminal 3: Submit orders
python run_complete_test.py
```

## 📈 How Results Were Calculated

### Latency Measurement
```python
order_start = time.time()
trades = await engine.process_order(order)
order_end = time.time()
latency = (order_end - order_start) * 1000  # Convert to milliseconds
```

### Throughput Calculation
```python
total_orders = 1000
total_time = end_time - start_time
throughput = total_orders / total_time  # orders per second
```

### Statistical Analysis
- **Average**: Mean of all latency measurements
- **P95**: 95th percentile (95% of requests faster than this)
- **P99**: 99th percentile (99% of requests faster than this)
- **Success Rate**: (Processed Orders / Total Orders) × 100

## 🚀 Installation & Setup

### Prerequisites
- Python 3.11+
- pip (Python package manager)

### 1. Clone and Setup
```bash
git clone <repository-url>
cd matching-engine

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Server
```bash
python src/main.py
```

### 3. Test the System
```bash
# Run unit tests
python -m pytest tests/ -v

# Run integration test
python run_complete_test.py

# Run performance benchmark
python performance/quick_benchmark.py
```

## 🎯 API Usage

### REST API Endpoints

**Submit Order**
```bash
curl -X POST http://localhost:5000/order \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTC-USDT",
    "order_type": "limit",
    "side": "buy",
    "quantity": "1.5",
    "price": "50000.0"
  }'
```

**Get Order Book**
```bash
curl http://localhost:5000/orderbook/BTC-USDT
```

**Get Statistics**
```bash
curl http://localhost:5000/stats
```

### WebSocket API

**Connect**
```javascript
const ws = new WebSocket('ws://localhost:8765');
```

**Subscribe to Order Book**
```json
{
  "action": "subscribe_orderbook",
  "symbols": ["BTC-USDT"]
}
```

**Subscribe to Trades**
```json
{
  "action": "subscribe_trades", 
  "symbols": ["BTC-USDT"]
}
```

## 🔬 Key Implementation Details

### Order Book Data Structure
```python
class OrderBook:
    def __init__(self, symbol: str):
        self.bids: Dict[Decimal, PriceLevel] = {}  # Max-heap for prices
        self.asks: Dict[Decimal, PriceLevel] = {}  # Min-heap for prices
        self.bid_prices = []  # Negative prices for max-heap
        self.ask_prices = []  # Regular prices for min-heap
```

### Matching Algorithm
1. **Price Priority**: Better prices execute first
2. **Time Priority**: Same price → first-in, first-out
3. **Trade-Through Protection**: Always match at best available price
4. **Order Type Handling**: Specific rules for MARKET, IOC, FOK

### Concurrency Model
- **Main Thread**: WebSocket server and event loop
- **Thread Pool**: Order processing (4 workers)
- **Async I/O**: Non-blocking WebSocket communication

## 🎯 What Was Achieved

### ✅ Core Requirements Met
- [x] REG NMS-inspired price-time priority
- [x] Internal order protection (no trade-throughs)
- [x] Multiple order types (Limit, Market, IOC, FOK)
- [x] Real-time BBO calculation and dissemination
- [x] REST API for order management
- [x] WebSocket for market data streaming
- [x] Trade execution reporting
- [x] Comprehensive error handling
- [x] Unit tests and documentation

### ✅ Performance Targets Exceeded
- **Target**: >1,000 orders/second
- **Achieved**: 1,200-1,800 orders/second
- **Latency**: Sub-5ms for 95% of orders
- **Stability**: Handles 10,000+ orders without degradation

### ✅ Code Quality
- Clean, maintainable architecture
- Comprehensive test coverage
- Detailed documentation
- Performance benchmarking suite

## 🚀 Future Enhancements

### Short-term Improvements
1. **Advanced Order Types**
   - Stop-Loss orders
   - Stop-Limit orders  
   - Take-Profit orders
   - Trailing stops

2. **Enhanced Persistence**
   ```python
   # Order book snapshotting
   def save_snapshot(self):
       with open(f"orderbook_{self.symbol}.json", 'w') as f:
           json.dump(self.to_dict(), f)
   
   def load_snapshot(self):
       # Recovery from disk
       pass
   ```

3. **Fee Model Implementation**
   ```python
   class FeeModel:
       def calculate_fee(self, trade: Trade, side: str) -> Decimal:
           # Maker-taker fee structure
           if side == 'maker':
               return trade.quantity * trade.price * self.maker_fee
           else:
               return trade.quantity * trade.price * self.taker_fee
   ```

### Medium-term Enhancements
4. **Multi-asset Support**
   - Cross-pair trading
   - Portfolio management
   - Risk controls per symbol

5. **Risk Management**
   ```python
   class RiskManager:
       def validate_order(self, order: Order) -> bool:
           # Position limits
           # Credit checks
           # Volatility controls
           pass
   ```

6. **Market Data Protocols**
   - FIX protocol support
   - Binary protocols for lower latency
   - Compression for bandwidth efficiency

### Long-term Vision
7. **Distributed Architecture**
   - Sharded order books
   - Load balancing across multiple engines
   - High availability with failover

8. **Regulatory Compliance**
   - Audit trails
   - Reporting systems
   - Compliance monitoring

9. **Advanced Analytics**
   - Real-time risk analytics
   - Market making algorithms
   - Predictive order routing

## 🔧 Performance Optimization Opportunities

### Current Bottlenecks
1. **GIL Limitations**: Python's Global Interpreter Limit
2. **Decimal Operations**: Slower than integer math
3. **Heap Operations**: O(log n) for price level management

### Potential Optimizations
1. **C++ Extension**: Critical path in C++ for 10x performance
2. **Integer Arithmetic**: Use integers instead of decimals (fixed-point)
3. **Lock-free Data Structures**: Reduce contention in concurrent access
4. **Memory Pool**: Object reuse to reduce GC pressure

## 📚 Learning Outcomes

### Technical Skills Gained
- Financial exchange architecture
- Order matching algorithms
- Real-time systems design
- Performance optimization
- WebSocket programming
- REST API design
- Concurrent programming patterns
- Decimal arithmetic for finance

### Domain Knowledge
- REG NMS regulations and principles
- Market microstructure
- Order book dynamics
- Trade execution logic
- Financial data streaming

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is for educational purposes. Please ensure proper licensing for production use.

## 🙏 Acknowledgments

- REG NMS regulations for guiding principles
- Modern exchange architecture patterns
- Python ecosystem for robust development tools

---

**Built with ❤️ for high-performance financial systems**

For questions or contributions, please open an issue or reach out to the development team.