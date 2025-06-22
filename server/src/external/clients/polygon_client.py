import os
import time
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dotenv import load_dotenv
from polygon import RESTClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class PolygonClient:
    def __init__(self):
        self.api_key = os.environ.get("POLYGON_API_KEY")
        if not self.api_key:
            raise ValueError("POLYGON_API_KEY environment variable is not set")
        
        self.client = RESTClient(api_key=self.api_key)
        self.rate_limit = 200  # requests per minute for free tier
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
                logger.info(f"Rate limit reached, waiting {wait_time} seconds...")
                time.sleep(wait_time)
                self.requests = []
        
        self.requests.append(now)
    
    def get_stock_price(self, symbol: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get historical stock prices using aggregates (bars)."""
        self._wait_for_rate_limit()
        
        try:
            # Get daily aggregates
            aggs = list(self.client.list_aggs(
                ticker=symbol,
                multiplier=1,
                timespan="day",
                from_=start_date,
                to=end_date,
                limit=50000
            ))
            
            if not aggs:
                return {"s": "no_data", "t": [], "o": [], "h": [], "l": [], "c": [], "v": []}
            
            # Convert to FinnHub format
            timestamps = []
            opens = []
            highs = []
            lows = []
            closes = []
            volumes = []
            
            for agg in aggs:
                # Polygon returns timestamp in milliseconds, convert to seconds for FinnHub compatibility
                timestamps.append(int(agg.timestamp / 1000))
                opens.append(float(agg.open))
                highs.append(float(agg.high))
                lows.append(float(agg.low))
                closes.append(float(agg.close))
                volumes.append(int(agg.volume))
            
            return {
                "s": "ok",
                "t": timestamps,
                "o": opens,
                "h": highs,
                "l": lows,
                "c": closes,
                "v": volumes
            }
            
        except Exception as e:
            logger.error(f"Error getting stock price for {symbol}: {str(e)}")
            return {"s": "error", "message": str(e)}
    
    def get_company_profile(self, symbol: str) -> Dict[str, Any]:
        """Get company profile using ticker details."""
        self._wait_for_rate_limit()
        
        try:
            ticker_details = self.client.get_ticker_details(symbol)
            
            # Handle address safely
            address_data = {}
            if hasattr(ticker_details, 'address') and ticker_details.address:
                address_data = ticker_details.address if isinstance(ticker_details.address, dict) else {}
            
            profile = {
                "name": getattr(ticker_details, 'name', ''),
                "ticker": getattr(ticker_details, 'ticker', symbol),
                "exchange": getattr(ticker_details, 'primary_exchange', ''),
                "ipo": getattr(ticker_details, 'list_date', ''),
                "marketCapitalization": getattr(ticker_details, 'market_cap', None),
                "shareOutstanding": getattr(ticker_details, 'share_class_shares_outstanding', None),
                "currency": getattr(ticker_details, 'currency_name', 'USD') or "USD",
                "country": getattr(ticker_details, 'locale', ''),
                "finnhubIndustry": getattr(ticker_details, 'sic_description', ''),
                "weburl": getattr(ticker_details, 'homepage_url', ''),
                "logo": getattr(ticker_details, 'icon_url', ''),
                "phone": getattr(ticker_details, 'phone_number', ''),
                "address": address_data,
                "city": address_data.get("city"),
                "state": address_data.get("state"),
                "description": getattr(ticker_details, 'description', ''),
                "employees": getattr(ticker_details, 'total_employees', None)
            }
            
            return profile
            
        except Exception as e:
            logger.error(f"Error getting company profile for {symbol}: {str(e)}")
            return {}
    
    def get_financial_statements(self, symbol: str, statement: str = "income") -> Dict[str, Any]:
        """Get financial statements."""
        self._wait_for_rate_limit()
        
        try:
            # Map statement types
            statement_type_map = {
                "income": "income_statement",
                "balance": "balance_sheet", 
                "cash": "cash_flow_statement"
            }
            
            financials_type = statement_type_map.get(statement, "income_statement")
            
            # Get financial data
            financials = list(self.client.vx.list_stock_financials(
                ticker=symbol,
                period_of_report_gte="2020-01-01",
                limit=10
            ))
            
            if not financials:
                return {"financials": []}
            
            # Convert to FinnHub format
            result = {"financials": []}
            for financial in financials:
                result["financials"].append({
                    "year": financial.period_of_report_date.year,
                    "quarter": financial.fiscal_quarter,
                    "period": financial.period_of_report_date.strftime("%Y-%m-%d"),
                    "financials": financial.financials
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting financial statements for {symbol}: {str(e)}")
            return {"financials": []}
    
    def get_basic_financials(self, symbol: str, period: str = "ttm", limit: int = 10) -> Dict[str, Any]:
        """Get basic financial metrics."""
        self._wait_for_rate_limit()
        
        try:
            # Get ticker details for basic metrics
            ticker_details = self.client.get_ticker_details(symbol)
            
            # Get financial data
            financials = list(self.client.vx.list_stock_financials(
                ticker=symbol,
                period_of_report_gte="2020-01-01",
                limit=limit
            ))
            
            metrics = {}
            series = {"annual": {}, "quarterly": {}}
            
            # Add basic metrics from ticker details
            if ticker_details:
                metrics["marketCapitalization"] = ticker_details.market_cap
                metrics["shareOutstanding"] = ticker_details.share_class_shares_outstanding
                
            # Process financial data
            for financial in financials:
                if financial.financials:
                    # Determine period type
                    period_key = "quarterly" if financial.fiscal_quarter else "annual"
                    
                    # Add metrics with period suffix
                    suffix = "TTM" if period.lower() == "ttm" else "Annual"
                    
                    for key, value in financial.financials.items():
                        if isinstance(value, (int, float)):
                            metric_key = f"{key}{suffix}"
                            metrics[metric_key] = value
                            
                            # Add to series
                            if key not in series[period_key]:
                                series[period_key][key] = []
                            series[period_key][key].append({
                                "period": financial.period_of_report_date.strftime("%Y-%m-%d"),
                                "v": value
                            })
            
            return {
                "metric": metrics,
                "series": series
            }
            
        except Exception as e:
            logger.error(f"Error getting basic financials for {symbol}: {str(e)}")
            return {"metric": {}, "series": {}}
    
    def get_insider_transactions(self, symbol: str, from_date: str = None, to_date: str = None) -> Dict[str, Any]:
        """Get insider transactions."""
        self._wait_for_rate_limit()
        
        try:
            # Build query parameters
            params = {}
            if from_date:
                params["filing_date.gte"] = from_date
            if to_date:
                params["filing_date.lte"] = to_date
            
            # Get insider transactions
            insider_transactions = list(self.client.vx.list_insider_transactions(
                ticker=symbol,
                limit=1000,
                **params
            ))
            
            # Convert to FinnHub format
            transactions = []
            for transaction in insider_transactions:
                transactions.append({
                    "symbol": symbol,
                    "name": transaction.owner_name,
                    "title": transaction.owner_title,
                    "transactionDate": transaction.transaction_date.strftime("%Y-%m-%d"),
                    "transactionCode": transaction.transaction_code,
                    "transactionShares": transaction.transaction_shares,
                    "transactionPrice": transaction.transaction_price_per_share,
                    "change": transaction.transaction_shares,
                    "price": transaction.transaction_price_per_share,
                    "filingDate": transaction.filing_date.strftime("%Y-%m-%d")
                })
            
            return {"data": transactions}
            
        except Exception as e:
            logger.error(f"Error getting insider transactions for {symbol}: {str(e)}")
            return {"data": []}
    
    def get_company_news(self, symbol: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get company news."""
        self._wait_for_rate_limit()
        
        try:
            # Get news
            news_items = list(self.client.list_ticker_news(
                ticker=symbol,
                published_utc_gte=start_date,
                published_utc_lte=end_date,
                limit=1000
            ))
            
            # Convert to FinnHub format
            news = []
            for item in news_items:
                news.append({
                    "category": item.category,
                    "datetime": int(item.published_utc.timestamp()),
                    "headline": item.title,
                    "id": item.id,
                    "image": item.image_url,
                    "related": symbol,
                    "source": item.publisher.name if item.publisher else "",
                    "summary": item.description,
                    "url": item.article_url,
                    "sentiment": 0  # Polygon doesn't provide sentiment
                })
            
            return news
            
        except Exception as e:
            logger.error(f"Error getting company news for {symbol}: {str(e)}")
            return []
    
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get real-time quote."""
        self._wait_for_rate_limit()
        
        try:
            # Get last quote
            quote = self.client.get_last_quote(symbol)
            
            # Get last trade for additional data
            trade = self.client.get_last_trade(symbol)
            
            # Get ticker details for market cap
            ticker_details = self.client.get_ticker_details(symbol)
            
            return {
                "c": trade.price if trade else None,  # current price
                "h": None,  # high price of the day
                "l": None,  # low price of the day
                "o": None,  # open price of the day
                "pc": None,  # previous close price
                "t": int(trade.participant_timestamp / 1000000) if trade else None,  # timestamp
                "dp": None,  # change
                "d": None,  # change percent
                "marketCap": ticker_details.market_cap if ticker_details else None
            }
            
        except Exception as e:
            logger.error(f"Error getting quote for {symbol}: {str(e)}")
            return {}
    
    def get_technical_indicators(self, symbol: str, indicator: str, 
                               start_date: str, end_date: str) -> Dict[str, Any]:
        """Get technical indicators."""
        self._wait_for_rate_limit()
        
        try:
            # Get technical indicators
            indicators = list(self.client.get_technical_indicator(
                ticker=symbol,
                indicator_name=indicator,
                timestamp_gte=start_date,
                timestamp_lte=end_date
            ))
            
            # Convert to FinnHub format
            result = {
                "s": "ok" if indicators else "no_data",
                indicator: []
            }
            
            for ind in indicators:
                result[indicator].append(ind.value)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting technical indicators for {symbol}: {str(e)}")
            return {"s": "error"}
    
    def get_reported_financials(self, symbol: str, freq: str = "annual") -> Dict[str, Any]:
        """Get historical reported financials."""
        self._wait_for_rate_limit()
        
        try:
            # Get financial data
            financials = list(self.client.vx.list_stock_financials(
                ticker=symbol,
                period_of_report_gte="2020-01-01",
                limit=20
            ))
            
            # Filter by frequency
            filtered_financials = []
            for financial in financials:
                if freq == "annual" and financial.fiscal_quarter is None:
                    filtered_financials.append(financial)
                elif freq == "quarterly" and financial.fiscal_quarter is not None:
                    filtered_financials.append(financial)
            
            # Convert to FinnHub format
            result = {"data": []}
            for financial in filtered_financials:
                result["data"].append({
                    "symbol": symbol,
                    "year": financial.fiscal_year,
                    "quarter": financial.fiscal_quarter,
                    "period": financial.period_of_report_date.strftime("%Y-%m-%d"),
                    "report": financial.financials
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting reported financials for {symbol}: {str(e)}")
            return {"data": []}
    
    def get_income_statement(self, symbol: str, freq: str = "annual") -> Dict[str, Any]:
        """Get historical income statements."""
        return self.get_financial_statements(symbol, "income")
    
    def get_balance_sheet(self, symbol: str, freq: str = "annual") -> Dict[str, Any]:
        """Get historical balance sheets."""
        return self.get_financial_statements(symbol, "balance")
    
    def get_cash_flow_statement(self, symbol: str, freq: str = "annual") -> Dict[str, Any]:
        """Get historical cash flow statements."""
        return self.get_financial_statements(symbol, "cash")
    
    def get_historical_financial_metrics(self, symbol: str, metric: str = "all") -> Dict[str, Any]:
        """Get historical financial metrics with time series data."""
        return self.get_basic_financials(symbol) 