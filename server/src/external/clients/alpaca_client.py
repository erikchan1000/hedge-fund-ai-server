import os
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class AlpacaClient:
    def __init__(self):
        self.api_key = os.environ.get("ALPACA_API_KEY")
        self.api_secret = os.environ.get("ALPACA_API_SECRET")
        if not self.api_key or not self.api_secret:
            raise ValueError("ALPACA_API_KEY and ALPACA_API_SECRET environment variables must be set")
        
        # Create headers
        self.headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.api_secret
        }
        self.base_url = "https://data.alpaca.markets/v2"
    
    def get_stock_price(self, symbol: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get historical stock prices from Alpaca."""
        try:
            # Convert dates to ISO format
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").isoformat() + "Z"
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").isoformat() + "Z"
            
            # Make request to Alpaca API
            url = f"{self.base_url}/stocks/bars"
            params = {
                "symbols": symbol,
                "timeframe": "1Day",
                "start": start_dt,
                "end": end_dt,
                "limit": 1000
            }
            
            response = requests.get(
                url,
                params=params,
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get("bars", {}).get(symbol):
                raise Exception(f"No price data found for {symbol}")
            
            # Convert Alpaca format to our expected format
            bars = data["bars"][symbol]
            return {
                "s": "ok",
                "t": [int(datetime.fromisoformat(bar["t"].replace("Z", "+00:00")).timestamp()) for bar in bars],
                "o": [bar["o"] for bar in bars],
                "h": [bar["h"] for bar in bars],
                "l": [bar["l"] for bar in bars],
                "c": [bar["c"] for bar in bars],
                "v": [bar["v"] for bar in bars]
            }
            
        except Exception as e:
            logger.error(f"Error fetching stock price from Alpaca for {symbol}: {str(e)}")
            raise 