import os
import time
import logging
from typing import Optional, Dict, Any, List
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class FinnHubClient:
    def __init__(self):
        self.api_key = os.environ.get("FINNHUB_API_KEY")
        if not self.api_key:
            raise ValueError("FINNHUB_API_KEY environment variable is not set")
        
        self.base_url = "https://finnhub.io/api/v1"
        self.rate_limit = 60  # requests per minute
        self.requests = []
        
    def _wait_for_rate_limit(self):
        """Implement rate limiting logic."""
        now = datetime.now()
        # Remove requests older than 1 minute
        self.requests = [req_time for req_time in self.requests 
                        if now - req_time < timedelta(minutes=1)]
        
        if len(self.requests) >= self.rate_limit:
            # Calculate time to wait
            oldest_request = self.requests[0]
            wait_time = 60 - (now - oldest_request).total_seconds()
            if wait_time > 0:
                time.sleep(wait_time)
                self.requests = []
        
        self.requests.append(now)
    
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a request to FinnHub API with rate limiting."""
        self._wait_for_rate_limit()
        
        url = f"{self.base_url}/{endpoint}"
        params = params or {}
        
        # Add API key as token parameter (correct FinnHub authentication method)
        params["token"] = self.api_key
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to {endpoint}: {str(e)}")
            raise
    
    def get_stock_price(self, symbol: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get historical stock prices."""
        # Convert dates to timestamps
        start_timestamp = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
        end_timestamp = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())
        
        return self._make_request("stock/candle", {
            "symbol": symbol,
            "resolution": "D",  # daily
            "from": start_timestamp,
            "to": end_timestamp
        })
    
    def get_company_profile(self, symbol: str) -> Dict[str, Any]:
        """Get company profile and basic financials."""
        return self._make_request("stock/profile2", {"symbol": symbol})
    
    def get_financial_statements(self, symbol: str, statement: str = "income") -> Dict[str, Any]:
        """Get financial statements using metric endpoint for processed data."""
        # Use the metric endpoint which provides standardized financial metrics
        return self._make_request("stock/metric", {
            "symbol": symbol,
            "metric": "all"  # Get all available metrics
        })
    
    def get_basic_financials(self, symbol: str) -> Dict[str, Any]:
        """Get basic financial metrics using the correct endpoint."""
        return self._make_request("stock/metric", {
            "symbol": symbol,
            "metric": "all"
        })
    
    def get_insider_transactions(self, symbol: str) -> Dict[str, Any]:
        """Get insider transactions."""
        return self._make_request("stock/insider-transactions", {"symbol": symbol})
    
    def get_company_news(self, symbol: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get company news."""
        return self._make_request("company-news", {
            "symbol": symbol,
            "from": start_date,
            "to": end_date
        })
    
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get real-time quote."""
        return self._make_request("quote", {"symbol": symbol})
    
    def get_technical_indicators(self, symbol: str, indicator: str, 
                               start_date: str, end_date: str) -> Dict[str, Any]:
        """Get technical indicators."""
        start_timestamp = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
        end_timestamp = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())
        
        return self._make_request("indicator", {
            "symbol": symbol,
            "resolution": "D",
            "from": start_timestamp,
            "to": end_timestamp,
            "indicator": indicator
        }) 