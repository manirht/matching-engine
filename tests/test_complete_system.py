import asyncio
import requests
import websockets
import json
import time
import threading

BASE_URL = "http://localhost:5000"

class WebSocketListener:
    def __init__(self):
        self.messages = []
        self.running = False
        
    async def start_listening(self):
        """Start listening to WebSocket messages"""
        self.running = True
        uri = "ws://localhost:8765"
        
        try:
            async with websockets.connect(uri) as websocket:
                # Subscribe to order book and trades
                await websocket.send(json.dumps({
                    "action": "subscribe_orderbook",
                    "symbols": ["BTC-USDT"]
                }))
                await websocket.send(json.dumps({
                    "action": "subscribe_trades",
                    "symbols": ["BTC-USDT"]
                }))
                
                print("🔌 WebSocket connected and subscribed")
                
                # Listen for messages
                while self.running:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        data = json.loads(message)
                        self.messages.append(data)
                        self.print_message(data)
                    except asyncio.TimeoutError:
                        continue
                        
        except Exception as e:
            print(f"WebSocket error: {e}")
    
    def print_message(self, data):
        """Print formatted WebSocket messages"""
        if data["type"] == "order_book_update":
            print(f"📊 OrderBook: {data['data']['symbol']} | "
                  f"Bid: {data['data']['best_bid'] or 'None'} | "
                  f"Ask: {data['data']['best_ask'] or 'None'}")
                  
        elif data["type"] == "trade_execution":
            trade = data['data']
            print(f"💰 Trade: {trade['quantity']} @ {trade['price']} | "
                  f"Side: {trade['aggressor_side']} | ID: {trade['trade_id'][:8]}...")
                  
        elif data["type"] == "order_book_snapshot":
            print(f"📈 Snapshot: {data['data']['symbol']} | "
                  f"Bids: {len(data['data']['bids'])} | "
                  f"Asks: {len(data['data']['asks'])}")

def submit_test_orders():
    """Submit test orders via REST API"""
    print("\n📤 Submitting test orders...")
    
    orders = [
        {
            "symbol": "BTC-USDT",
            "order_type": "limit",
            "side": "buy",
            "quantity": "2.0",
            "price": "50000.0"
        },
        {
            "symbol": "BTC-USDT", 
            "order_type": "limit",
            "side": "sell",
            "quantity": "1.5", 
            "price": "50000.0"
        },
        {
            "symbol": "BTC-USDT",
            "order_type": "limit", 
            "side": "buy",
            "quantity": "1.0",
            "price": "49000.0"
        },
        {
            "symbol": "BTC-USDT",
            "order_type": "limit",
            "side": "sell", 
            "quantity": "0.8",
            "price": "51000.0"
        }
    ]
    
    for i, order_data in enumerate(orders):
        try:
            response = requests.post(f"{BASE_URL}/order", json=order_data, timeout=5)
            result = response.json()
            print(f"   Order {i+1}: {result['status']} - {len(result['trades'])} trades")
            
            if result['trades']:
                for trade in result['trades']:
                    print(f"      🎯 Trade: {trade['quantity']} @ {trade['price']}")
                    
        except Exception as e:
            print(f"   Order {i+1} failed: {e}")
        
        time.sleep(1)  # Wait between orders
    
    # Check final state
    print("\n📋 Final State:")
    try:
        order_book = requests.get(f"{BASE_URL}/orderbook/BTC-USDT").json()
        print(f"   Order Book - Bid: {order_book['best_bid']}, Ask: {order_book['best_ask']}")
        
        stats = requests.get(f"{BASE_URL}/stats").json()
        print(f"   Stats - Processed: {stats['processed_orders']}, OPS: {stats['orders_per_second']:.2f}")
    except Exception as e:
        print(f"   Error getting state: {e}")

async def main():
    """Main test function"""
    print("🚀 Starting Complete System Test")
    print("=" * 50)
    
    # Start WebSocket listener
    listener = WebSocketListener()
    
    # Run WebSocket listener in background
    websocket_task = asyncio.create_task(listener.start_listening())
    
    # Wait for WebSocket to connect
    await asyncio.sleep(2)
    
    # Submit orders in a separate thread to not block
    order_thread = threading.Thread(target=submit_test_orders)
    order_thread.start()
    
    # Wait for orders to complete
    order_thread.join()
    
    # Keep listening for a bit more to catch any delayed messages
    print("\n👂 Listening for additional updates (5 seconds)...")
    await asyncio.sleep(5)
    
    # Stop WebSocket listener
    listener.running = False
    websocket_task.cancel()
    
    print("\n✅ Test completed!")
    print(f"📨 Total WebSocket messages received: {len(listener.messages)}")

if __name__ == "__main__":
    asyncio.run(main())