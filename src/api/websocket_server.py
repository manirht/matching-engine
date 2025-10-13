import asyncio
import json
import logging
from typing import Set, Dict, List
import websockets
from websockets.server import WebSocketServerProtocol
from datetime import datetime, timezone

from src.engine.matching_engine import MatchingEngine
from src.models.trade import Trade

class MarketDataWebSocket:
    def __init__(self, matching_engine: MatchingEngine, host: str = "localhost", port: int = 8765):
        self.matching_engine = matching_engine
        self.host = host
        self.port = port
        self.connections: Set[WebSocketServerProtocol] = set()
        self.subscriptions: Dict[WebSocketServerProtocol, Set[str]] = {}
        self.trade_subscriptions: Dict[WebSocketServerProtocol, Set[str]] = {}
        
        self.logger = logging.getLogger("MarketDataWebSocket")
    
    async def start_server(self):
        """Start WebSocket server"""
        self.logger.info(f"Starting WebSocket server on {self.host}:{self.port}")
        return await websockets.serve(self.handle_connection, self.host, self.port)
    
    async def handle_connection(self, websocket: WebSocketServerProtocol, path: str):
        """Handle new WebSocket connection"""
        self.connections.add(websocket)
        self.subscriptions[websocket] = set()
        self.trade_subscriptions[websocket] = set()
        
        try:
            # Send welcome message
            await websocket.send(json.dumps({
                "type": "welcome",
                "message": "Connected to Matching Engine WebSocket",
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
            }))
            
            async for message in websocket:
                await self.handle_message(websocket, message)
                
        except websockets.exceptions.ConnectionClosed:
            self.logger.info("WebSocket connection closed")
        except Exception as e:
            self.logger.error(f"WebSocket error: {e}")
        finally:
            # Clean up on disconnect
            self.connections.remove(websocket)
            if websocket in self.subscriptions:
                del self.subscriptions[websocket]
            if websocket in self.trade_subscriptions:
                del self.trade_subscriptions[websocket]
    
    async def handle_message(self, websocket: WebSocketServerProtocol, message: str):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            action = data.get("action")
            
            if action == "subscribe_orderbook":
                symbols = data.get("symbols", [])
                if isinstance(symbols, str):
                    symbols = [symbols]
                self.subscriptions[websocket].update(symbols)
                await websocket.send(json.dumps({
                    "type": "subscription",
                    "status": "subscribed", 
                    "channel": "orderbook",
                    "symbols": list(symbols),
                    "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
                }))
                
                # Send initial order book state for subscribed symbols
                for symbol in symbols:
                    order_book_data = self.matching_engine.get_order_book_state(symbol)
                    if order_book_data:
                        await websocket.send(json.dumps({
                            "type": "order_book_snapshot",
                            "data": order_book_data
                        }))
            
            elif action == "subscribe_trades":
                symbols = data.get("symbols", [])
                if isinstance(symbols, str):
                    symbols = [symbols]
                self.trade_subscriptions[websocket].update(symbols)
                await websocket.send(json.dumps({
                    "type": "subscription",
                    "status": "subscribed",
                    "channel": "trades", 
                    "symbols": list(symbols),
                    "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
                }))
            
            elif action == "unsubscribe_orderbook":
                symbols = data.get("symbols", [])
                if isinstance(symbols, str):
                    symbols = [symbols]
                self.subscriptions[websocket].difference_update(symbols)
                await websocket.send(json.dumps({
                    "type": "subscription",
                    "status": "unsubscribed",
                    "channel": "orderbook",
                    "symbols": list(symbols),
                    "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
                }))
                
            elif action == "unsubscribe_trades":
                symbols = data.get("symbols", [])
                if isinstance(symbols, str):
                    symbols = [symbols]
                self.trade_subscriptions[websocket].difference_update(symbols)
                await websocket.send(json.dumps({
                    "type": "subscription", 
                    "status": "unsubscribed",
                    "channel": "trades",
                    "symbols": list(symbols),
                    "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
                }))
            
            elif action == "list_subscriptions":
                await websocket.send(json.dumps({
                    "type": "subscription_list",
                    "orderbook_symbols": list(self.subscriptions[websocket]),
                    "trade_symbols": list(self.trade_subscriptions[websocket]),
                    "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
                }))
                
            else:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": f"Unknown action: {action}",
                    "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
                }))
                
        except json.JSONDecodeError:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "Invalid JSON message",
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
            }))
    
    async def broadcast_order_book_update(self, symbol: str):
        """Broadcast order book update to subscribed clients"""
        if not self.connections:
            return
        
        order_book_data = self.matching_engine.get_order_book_state(symbol)
        if not order_book_data:
            return
        
        message = json.dumps({
            "type": "order_book_update",
            "data": order_book_data
        })
        
        tasks = []
        for websocket, subscriptions in self.subscriptions.items():
            if symbol in subscriptions:
                tasks.append(websocket.send(message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast_trade(self, trade: Trade):
        """Broadcast trade execution to subscribed clients"""
        if not self.connections:
            return
        
        message = json.dumps({
            "type": "trade_execution",
            "data": trade.to_dict()
        })
        
        tasks = []
        for websocket, subscriptions in self.trade_subscriptions.items():
            if trade.symbol in subscriptions:
                tasks.append(websocket.send(message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)