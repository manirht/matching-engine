from flask import Flask, request, jsonify
from decimal import Decimal, InvalidOperation
import logging
from datetime import datetime, timezone
import uuid

from src.models.order import Order, OrderSide, OrderType
from src.engine.matching_engine import MatchingEngine

class RESTAPI:
    def __init__(self, matching_engine: MatchingEngine):
        self.matching_engine = matching_engine
        self.app = Flask(__name__)
        self.setup_routes()
        self.logger = logging.getLogger("RESTAPI")
    
    def setup_routes(self):
        @self.app.route('/order', methods=['POST'])
        def submit_order():
            try:
                data = request.get_json()
                
                # Validate required fields
                required_fields = ['symbol', 'order_type', 'side', 'quantity']
                for field in required_fields:
                    if field not in data:
                        return jsonify({"error": f"Missing required field: {field}"}), 400
                
                # Parse order data
                symbol = data['symbol']
                order_type = OrderType(data['order_type'])
                side = OrderSide(data['side'])
                
                try:
                    quantity = Decimal(str(data['quantity']))
                except InvalidOperation:
                    return jsonify({"error": "Invalid quantity format"}), 400
                
                price = None
                if order_type == OrderType.LIMIT:
                    if 'price' not in data:
                        return jsonify({"error": "Limit orders require price"}), 400
                    try:
                        price = Decimal(str(data['price']))
                    except InvalidOperation:
                        return jsonify({"error": "Invalid price format"}), 400
                
                # Create order
                order = Order(
                    order_id=str(uuid.uuid4()),
                    symbol=symbol,
                    order_type=order_type,
                    side=side,
                    quantity=quantity,
                    price=price,
                    timestamp=datetime.now(timezone.utc),
                    user_id=data.get('user_id')
                )
                
                # Process order
                import asyncio
                trades = asyncio.run(self.matching_engine.process_order(order))
                
                response = {
                    "order_id": order.order_id,
                    "status": "accepted",
                    "trades": [trade.to_dict() for trade in trades]
                }
                
                return jsonify(response), 200
                
            except Exception as e:
                self.logger.error(f"Error processing order: {e}")
                return jsonify({"error": str(e)}), 400
        
        @self.app.route('/orderbook/<symbol>', methods=['GET'])
        def get_order_book(symbol: str):
            try:
                depth = request.args.get('depth', 10, type=int)
                order_book_data = self.matching_engine.get_order_book_state(symbol, depth)
                
                if not order_book_data:
                    return jsonify({"error": f"Symbol {symbol} not found"}), 404
                
                return jsonify(order_book_data), 200
                
            except Exception as e:
                self.logger.error(f"Error getting order book: {e}")
                return jsonify({"error": str(e)}), 400
        
        @self.app.route('/stats', methods=['GET'])
        def get_stats():
            stats = self.matching_engine.get_performance_stats()
            return jsonify(stats), 200
    
    def run(self, host: str = 'localhost', port: int = 5000, debug: bool = False):
        self.logger.info(f"Starting REST API on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug, use_reloader=False)