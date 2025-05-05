import os
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from dotenv import load_dotenv
from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

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
        
        # Initialize the historical data client
        self.client = StockHistoricalDataClient(self.api_key, self.api_secret)
    
    def get_stock_price(self, symbol: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get historical stock prices from Alpaca."""
        try:
            # Convert dates to datetime objects
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            # Create the request
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Day,
                start=start_dt,
                end=end_dt,
                limit=1000  # Maximum number of bars to return
            )
            
            # Get the bars
            bars = self.client.get_stock_bars(request)
            
            if not bars.data:
                raise Exception(f"No price data found for {symbol}")
            
            # Convert bars to list format
            bars_list = bars.data[symbol]
            
            # Convert Alpaca format to our expected format
            return {
                "s": "ok",
                "t": [int(bar.timestamp.timestamp()) for bar in bars_list],
                "o": [bar.open for bar in bars_list],
                "h": [bar.high for bar in bars_list],
                "l": [bar.low for bar in bars_list],
                "c": [bar.close for bar in bars_list],
                "v": [bar.volume for bar in bars_list]
            }
            
        except Exception as e:
            logger.error(f"Error fetching stock price from Alpaca for {symbol}: {str(e)}")
            raise 