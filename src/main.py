import asyncio
import logging
import signal
import sys
from threading import Thread

from src.engine.matching_engine import MatchingEngine
from src.api.websocket_server import MarketDataWebSocket
from src.api.rest_api import RESTAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('matching_engine.log')
    ]
)

class MatchingEngineApplication:
    def __init__(self):
        self.matching_engine = MatchingEngine()
        self.websocket_server = MarketDataWebSocket(self.matching_engine)
        self.rest_api = RESTAPI(self.matching_engine)
        
        # Connect WebSocket server to matching engine
        self.matching_engine.set_websocket_server(self.websocket_server)
        
        self.logger = logging.getLogger("Application")
    
    async def start(self):
        self.logger.info("Starting Matching Engine Application")
        
        # Start WebSocket server
        await self.websocket_server.start_server()
        
        # Start REST API in separate thread
        api_thread = Thread(target=self.rest_api.run, daemon=True)
        api_thread.start()
        
        self.logger.info("Application started successfully")
        self.logger.info("REST API available at: http://localhost:5000")
        self.logger.info("WebSocket server available at: ws://localhost:8765")
        self.logger.info("Use Ctrl+C to stop the application")
        
        # Keep the main thread alive
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Application stopped by user")

if __name__ == "__main__":
    app = MatchingEngineApplication()
    asyncio.run(app.start())