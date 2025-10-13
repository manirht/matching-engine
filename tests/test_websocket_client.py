import asyncio
import websockets
import json
import time

async def websocket_client():
    """Test WebSocket client for the matching engine"""
    uri = "ws://localhost:8765"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket server")
            
            # Subscribe to order book and trades for BTC-USDT
            subscribe_message = {
                "action": "subscribe_orderbook",
                "symbols": ["BTC-USDT"]
            }
            await websocket.send(json.dumps(subscribe_message))
            response = await websocket.recv()
            print(f"Subscription response: {json.loads(response)}")
            
            # Also subscribe to trades
            trade_subscribe = {
                "action": "subscribe_trades", 
                "symbols": ["BTC-USDT"]
            }
            await websocket.send(json.dumps(trade_subscribe))
            response = await websocket.recv()
            print(f"Trade subscription response: {json.loads(response)}")
            
            print("\nListening for real-time updates...")
            print("=" * 50)
            
            # Listen for messages for 30 seconds
            start_time = time.time()
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    
                    if data["type"] == "order_book_update":
                        print(f"\n📊 Order Book Update:")
                        print(f"   Symbol: {data['data']['symbol']}")
                        print(f"   Best Bid: {data['data']['best_bid']}")
                        print(f"   Best Ask: {data['data']['best_ask']}")
                        print(f"   Timestamp: {data['data']['timestamp']}")
                    
                    elif data["type"] == "trade_execution":
                        print(f"\n💰 Trade Execution:")
                        print(f"   Trade ID: {data['data']['trade_id']}")
                        print(f"   Price: {data['data']['price']}")
                        print(f"   Quantity: {data['data']['quantity']}")
                        print(f"   Side: {data['data']['aggressor_side']}")
                        print(f"   Timestamp: {data['data']['timestamp']}")
                    
                    elif data["type"] == "order_book_snapshot":
                        print(f"\n📈 Order Book Snapshot Received")
                        print(f"   Symbol: {data['data']['symbol']}")
                        print(f"   Bid Levels: {len(data['data']['bids'])}")
                        print(f"   Ask Levels: {len(data['data']['asks'])}")
                        
                except asyncio.TimeoutError:
                    # No message received, continue listening
                    continue
                
    except Exception as e:
        print(f"WebSocket error: {e}")

if __name__ == "__main__":
    asyncio.run(websocket_client())