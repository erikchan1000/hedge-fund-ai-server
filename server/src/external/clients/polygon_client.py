import os
import time
import logging
from dateutil.parser import parse
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dotenv import load_dotenv
from polygon import RESTClient
from src.utils.llm import APIRateLimiter
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from src.data.models import SentimentType

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def analyze_news_sentiment_batch(news_items: List[Dict[str, Any]], symbol: str) -> List[SentimentType]:
    """
    Analyze sentiment for a batch of news items using OpenAI.
    Returns a list of SentimentType enum values: POSITIVE, NEGATIVE, or NEUTRAL
    """
    if not news_items:
        return []
    
    try:
        # Get OpenAI API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not found. Returning neutral sentiment for all news items.")
            return [SentimentType.NEUTRAL] * len(news_items)
        
        # Initialize OpenAI client
        llm = ChatOpenAI(
            model="gpt-4o-mini",  # Using a cost-effective model for sentiment analysis
            api_key=api_key,
            temperature=0.1  # Low temperature for consistent sentiment classification
        )
        
        # Rate limiter for OpenAI API calls
        rate_limiter = APIRateLimiter("openai")
        rate_limiter.wait_for_rate_limit()
        
        # Prepare batch prompt
        news_text = ""
        for i, item in enumerate(news_items):
            headline = item.get('headline', '')
            summary = item.get('summary', '')
            news_text += f"{i+1}. Headline: {headline}\n"
            if summary:
                news_text += f"   Summary: {summary}\n"
            news_text += "\n"
        
        prompt = f"""Analyze the sentiment of the following news articles about {symbol}. 
For each article, determine if the sentiment is positive, negative, or neutral for the stock price.

Consider:
- Positive: Good earnings, partnerships, growth, upgrades, positive guidance
- Negative: Losses, lawsuits, downgrades, regulatory issues, poor earnings
- Neutral: General announcements, routine updates, mixed signals

Return only a comma-separated list of sentiments (positive, negative, or neutral) for each article in order.

News articles:
{news_text}

Response format: positive, negative, neutral, positive, ...
"""
        
        # Make the API call
        message = HumanMessage(content=prompt)
        response = llm.invoke([message])
        
        # Parse the response
        sentiment_text = response.content.strip()
        sentiments = [s.strip().lower() for s in sentiment_text.split(',')]
        
        # Validate and clean the results
        valid_sentiments = []
        for sentiment in sentiments:
            if sentiment == 'positive':
                valid_sentiments.append(SentimentType.POSITIVE)
            elif sentiment == 'negative':
                valid_sentiments.append(SentimentType.NEGATIVE)
            elif sentiment == 'neutral':
                valid_sentiments.append(SentimentType.NEUTRAL)
            else:
                # Default to neutral for invalid responses
                valid_sentiments.append(SentimentType.NEUTRAL)
        
        # Ensure we have the right number of sentiments
        while len(valid_sentiments) < len(news_items):
            valid_sentiments.append(SentimentType.NEUTRAL)
        
        return valid_sentiments[:len(news_items)]
        
    except Exception as e:
        logger.error(f"Error analyzing sentiment for {symbol}: {str(e)}")
        # Return neutral sentiment for all items on error
        return [SentimentType.NEUTRAL] * len(news_items)

class PolygonClient:
    def __init__(self):
        self.api_key = os.environ.get("POLYGON_API_KEY")
        if not self.api_key:
            raise ValueError("POLYGON_API_KEY environment variable is not set")
        
        self.client = RESTClient(api_key=self.api_key)
        self.rate_limit = 50  # More conservative: 50 requests per minute
        self.requests = []
        self.last_request_time = None
        
    def _wait_for_rate_limit(self):
        """Implement conservative rate limiting logic."""
        now = datetime.now()
        
        # Always wait at least 2 seconds between requests to be conservative
        if self.last_request_time:
            time_since_last = (now - self.last_request_time).total_seconds()
            if time_since_last < 2.0:
                wait_time = 2.0 - time_since_last
                logger.debug(f"Rate limiting: waiting {wait_time:.2f} seconds...")
                time.sleep(wait_time)
                now = datetime.now()
        
        # Remove requests older than 1 minute
        self.requests = [req_time for req_time in self.requests 
                        if now - req_time < timedelta(minutes=1)]
        
        if len(self.requests) >= self.rate_limit:
            # Calculate time to wait
            oldest_request = self.requests[0]
            wait_time = 60 - (now - oldest_request).total_seconds() + 5  # Add 5 second buffer
            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time:.2f} seconds...")
                time.sleep(wait_time)
                self.requests = []
                now = datetime.now()
        
        self.requests.append(now)
        self.last_request_time = now
    
    def _execute_with_retry(self, func, *args, max_retries=3, **kwargs):
        """Execute a function with exponential backoff retry on rate limit errors."""
        for attempt in range(max_retries + 1):
            try:
                self._wait_for_rate_limit()
                return func(*args, **kwargs)
            except Exception as e:
                error_str = str(e).lower()
                if "429" in error_str or "too many" in error_str or "rate limit" in error_str:
                    if attempt < max_retries:
                        # Exponential backoff: 5, 10, 20 seconds
                        wait_time = 5 * (2 ** attempt)
                        logger.warning(f"Rate limit hit (attempt {attempt + 1}/{max_retries + 1}), "
                                     f"waiting {wait_time} seconds before retry...")
                        time.sleep(wait_time)
                        # Clear request history to reset rate limiting
                        self.requests = []
                        continue
                    else:
                        logger.error(f"Max retries exceeded due to rate limiting: {str(e)}")
                        raise
                else:
                    # Non-rate-limit error, don't retry
                    raise
    
    def get_stock_price(self, symbol: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get historical stock prices using aggregates (bars)."""
        try:
            # Get daily aggregates
            aggs = list(self._execute_with_retry(
                self.client.list_aggs,
                ticker=symbol,
                multiplier=1,
                timespan="day",
                from_=start_date,
                to=end_date,
                limit=50
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
        try:
            ticker_details = self._execute_with_retry(
                self.client.get_ticker_details,
                symbol
            )
            
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
        try:
            # Get financial data using the vX endpoint
            financials = list(self._execute_with_retry(
                self.client.vx.list_stock_financials,
                ticker=symbol,
                period_of_report_date_gte="2020-01-01",
                limit=10
            ))
            
            if not financials:
                return {"financials": []}
            
            # Convert to FinnHub format
            result = {"financials": []}
            for financial in financials:
                # Convert Financials object to dictionary
                financials_obj = getattr(financial, 'financials', None)
                financials_dict = self._convert_financials_to_dict(financials_obj) if financials_obj else {}
                
                financial_data = {
                    "year": getattr(financial, 'fiscal_year', None),
                    "quarter": getattr(financial, 'fiscal_quarter', None),
                    "period": getattr(financial, 'period_of_report_date', ''),
                    "financials": financials_dict
                }
                
                # Convert period date to string if it's a date object
                if hasattr(financial, 'period_of_report_date') and financial.period_of_report_date:
                    try:
                        financial_data["period"] = financial.period_of_report_date.strftime("%Y-%m-%d")
                    except:
                        financial_data["period"] = str(financial.period_of_report_date)
                
                result["financials"].append(financial_data)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting financial statements for {symbol}: {str(e)}")
            return {"financials": []}
    
    def _extract_datapoint_value(self, datapoint) -> Optional[float]:
        """Extract value from a Polygon DataPoint object."""
        if datapoint is None:
            return None
        
        # Handle DataPoint objects
        if hasattr(datapoint, 'value'):
            value = getattr(datapoint, 'value', None)
            if value is not None and isinstance(value, (int, float)):
                return float(value)
        
        return None
    
    def _convert_financials_to_dict(self, financials_obj) -> Dict[str, Any]:
        """Convert Polygon Financials object to dictionary format with derived metrics."""
        result = {}
        
        if not financials_obj:
            return result
        
        # Process each financial statement section
        sections = ['balance_sheet', 'income_statement', 'cash_flow_statement', 'comprehensive_income']
        
        for section_name in sections:
            section_obj = getattr(financials_obj, section_name, None)
            if section_obj:
                # Get all attributes of the section object
                for attr_name in dir(section_obj):
                    if not attr_name.startswith('_'):  # Skip private attributes
                        attr_value = getattr(section_obj, attr_name, None)
                        
                        # Try to extract value from DataPoint
                        extracted_value = self._extract_datapoint_value(attr_value)
                        if extracted_value is not None:
                            # Create a meaningful key name
                            key = f"{section_name}_{attr_name}"
                            result[key] = extracted_value
        
        # Calculate derived financial metrics
        derived_metrics = self._calculate_derived_metrics(result)
        result.update(derived_metrics)
        
        return result
    
    def _calculate_derived_metrics(self, financial_data: Dict[str, float]) -> Dict[str, float]:
        """Calculate common financial ratios and metrics from raw financial data."""
        metrics = {}
        
        try:
            # Helper function to safely get values
            def safe_get(key: str) -> Optional[float]:
                value = financial_data.get(key)
                return value if value is not None and value != 0 else None
            
            # Get key financial statement items
            revenues = safe_get('income_statement_revenues')
            gross_profit = safe_get('income_statement_gross_profit')
            operating_income = safe_get('income_statement_operating_income_loss')
            net_income = safe_get('income_statement_net_income_loss')
            total_assets = safe_get('balance_sheet_assets')
            current_assets = safe_get('balance_sheet_current_assets')
            current_liabilities = safe_get('balance_sheet_current_liabilities')
            total_liabilities = safe_get('balance_sheet_liabilities')
            total_equity = safe_get('balance_sheet_equity')
            long_term_debt = safe_get('balance_sheet_long_term_debt')
            basic_shares = safe_get('income_statement_basic_average_shares')
            eps_basic = safe_get('income_statement_basic_earnings_per_share')
            eps_diluted = safe_get('income_statement_diluted_earnings_per_share')
            
            # Profitability Ratios
            if revenues and gross_profit:
                metrics['gross_margin'] = gross_profit / revenues
            
            if revenues and operating_income:
                metrics['operating_margin'] = operating_income / revenues
            
            if revenues and net_income:
                metrics['net_margin'] = net_income / revenues
            
            if net_income and total_equity:
                metrics['return_on_equity'] = net_income / total_equity
            
            if net_income and total_assets:
                metrics['return_on_assets'] = net_income / total_assets
            
            # Liquidity Ratios
            if current_assets and current_liabilities:
                metrics['current_ratio'] = current_assets / current_liabilities
            
            # Leverage Ratios
            if long_term_debt and total_equity:
                metrics['debt_to_equity'] = long_term_debt / total_equity
            
            if total_liabilities and total_assets:
                metrics['debt_to_assets'] = total_liabilities / total_assets
            
            if total_equity and total_assets:
                metrics['equity_ratio'] = total_equity / total_assets
            
            # Per Share Metrics
            if revenues and basic_shares and basic_shares != 0:
                # Convert shares to positive value if negative (some companies report as negative)
                shares = abs(basic_shares)
                metrics['revenue_per_share'] = revenues / shares
            
            if total_equity and basic_shares and basic_shares != 0:
                shares = abs(basic_shares)
                metrics['book_value_per_share'] = total_equity / shares
            
            # Efficiency Ratios
            if revenues and total_assets:
                metrics['asset_turnover'] = revenues / total_assets
            
            # Include EPS if available
            if eps_basic is not None:
                metrics['earnings_per_share_basic'] = eps_basic
            
            if eps_diluted is not None:
                metrics['earnings_per_share_diluted'] = eps_diluted
            
        except (ZeroDivisionError, TypeError) as e:
            logger.debug(f"Error calculating derived metrics: {e}")
        
        return metrics

    def get_basic_financials(self, symbol: str, period: str = "ttm", limit: int = 10) -> Dict[str, Any]:
        """Get basic financial metrics."""
        try:
            # Get ticker details for basic metrics
            ticker_details = self._execute_with_retry(
                self.client.get_ticker_details,
                symbol
            )
            # get last year date
            last_year_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            # Get financial data using the vX endpoint
            financials = list(self._execute_with_retry(
                self.client.vx.list_stock_financials,
                ticker=symbol,
                period_of_report_date_gte=last_year_date,
                limit=limit
            ))
            
            metrics = {}
            series = {"annual": {}, "quarterly": {}}
            
            # Add basic metrics from ticker details
            if ticker_details:
                metrics["marketCapitalization"] = getattr(ticker_details, 'market_cap', None)
                metrics["shareOutstanding"] = getattr(ticker_details, 'share_class_shares_outstanding', None)
                
            # Process each StockFinancial object to build time series
            for financial in financials:
                financial_data = getattr(financial, 'financials', None)
                if financial_data:
                    # Convert Financials object to dictionary
                    financial_dict = self._convert_financials_to_dict(financial_data)
                    
                    if financial_dict:
                        # Determine period type (quarterly vs annual)
                        fiscal_quarter = getattr(financial, 'fiscal_quarter', None)
                        period_key = "quarterly" if fiscal_quarter else "annual"
                        
                        # Get period date safely
                        period_date = getattr(financial, 'period_of_report_date', '')
                        if hasattr(period_date, 'strftime'):
                            period_str = period_date.strftime("%Y-%m-%d")
                        else:
                            period_str = str(period_date)
                        
                        # Process each metric in this financial period
                        for key, value in financial_dict.items():
                            if isinstance(value, (int, float)) and value is not None:
                                # Initialize series array for this metric if it doesn't exist
                                if key not in series[period_key]:
                                    series[period_key][key] = []
                                
                                # Add this period's data point to the time series
                                series[period_key][key].append({
                                    "period": period_str,
                                    "v": value
                                })
                                
                                # Update the latest metric value (for the metrics dict)
                                suffix = "TTM" if period.lower() == "ttm" else "Annual"
                                metric_key = f"{key}{suffix}"
                                
                                # Keep the most recent value (financials are usually ordered by date)
                                if metric_key not in metrics:
                                    metrics[metric_key] = value
            
            # Sort time series data by period date (most recent first)
            for period_type in series:
                for metric_name in series[period_type]:
                    series[period_type][metric_name].sort(
                        key=lambda x: x["period"], 
                        reverse=True
                    )
            
            return {
                "metric": metrics,
                "series": series
            }
            
        except Exception as e:
            logger.error(f"Error getting basic financials for {symbol}: {str(e)}")
            return {"metric": {}, "series": {}}
    
    def get_insider_transactions(self, symbol: str, from_date: str = None, to_date: str = None) -> Dict[str, Any]:
        """Insider transactions are not supported in this implementation."""
        logger.info(f"Insider transactions functionality has been removed from the algorithm")
        return {"data": []}
    
    def get_company_news(self, symbol: str, start_date: str, end_date: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get company news."""
        self._wait_for_rate_limit()
        
        try:
            # Get news using iterator but respect the limit parameter
            news_iterator = self.client.list_ticker_news(
                ticker=symbol,
                published_utc_gte=start_date,
                published_utc_lte=end_date,
                order="desc",
                limit=min(limit, 1000)  # Polygon API max limit per request
            )
            
            # Collect items until we reach the desired limit
            news_items = []
            for item in news_iterator:
                news_items.append(item)
                if len(news_items) >= limit:
                    break
            
            # Convert to FinnHub format first (without sentiment)
            news = []
            for item in news_items:
                # Handle publisher safely
                publisher_name = ""
                if hasattr(item, 'publisher') and item.publisher:
                    publisher_name = getattr(item.publisher, 'name', '') if hasattr(item.publisher, 'name') else str(item.publisher)
                
                # Handle published timestamp
                datetime_timestamp = 0
                if hasattr(item, 'published_utc') and item.published_utc:
                    try:
                        dt = parse(item.published_utc)
                        datetime_timestamp = int(dt.timestamp())
                    except:
                        datetime_timestamp = 0
                
                news.append({
                    "category": getattr(item, 'category', ''),
                    "datetime": datetime_timestamp,
                    "headline": getattr(item, 'title', ''),
                    "id": getattr(item, 'id', ''),
                    "image": getattr(item, 'image_url', ''),
                    "related": symbol,
                    "source": publisher_name,
                    "summary": getattr(item, 'description', ''),
                    "url": getattr(item, 'article_url', ''),
                    "sentiment": SentimentType.NEUTRAL  # Default sentiment, will be updated below
                })
            
            # Analyze sentiment for all news items in batch
            if news:
                logger.info(f"Analyzing sentiment for {len(news)} news items for {symbol}")
                sentiments = analyze_news_sentiment_batch(news, symbol)
                
                # Update sentiment for each news item
                for i, sentiment in enumerate(sentiments):
                    if i < len(news):
                        news[i]["sentiment"] = sentiment
            
            return news
            
        except Exception as e:
            logger.error(f"Error getting company news for {symbol}: {str(e)}")
            return []
    
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get real-time quote."""
        self._wait_for_rate_limit()
        
        try:
            # Get last trade for current price
            trade = None
            try:
                trade = self.client.get_last_trade(symbol)
            except Exception as e:
                logger.warning(f"Could not get last trade for {symbol}: {str(e)}")
            
            # Get ticker details for market cap
            ticker_details = None
            try:
                ticker_details = self.client.get_ticker_details(symbol)
            except Exception as e:
                logger.warning(f"Could not get ticker details for {symbol}: {str(e)}")
            
            # Build response in FinnHub format
            current_price = None
            timestamp = None
            market_cap = None
            
            if trade:
                current_price = getattr(trade, 'price', None)
                # Convert nanosecond timestamp to seconds
                if hasattr(trade, 'participant_timestamp'):
                    timestamp = int(getattr(trade, 'participant_timestamp', 0) / 1000000000)
                elif hasattr(trade, 'timestamp'):
                    timestamp = int(getattr(trade, 'timestamp', 0) / 1000000000)
            
            if ticker_details:
                market_cap = getattr(ticker_details, 'market_cap', None)
            
            return {
                "c": current_price,  # current price
                "h": None,  # high price of the day (not available from this endpoint)
                "l": None,  # low price of the day (not available from this endpoint)
                "o": None,  # open price of the day (not available from this endpoint)
                "pc": None,  # previous close price (not available from this endpoint)
                "t": timestamp,  # timestamp
                "dp": None,  # change (not available from this endpoint)
                "d": None,  # change percent (not available from this endpoint)
                "marketCap": market_cap
            }
            
        except Exception as e:
            logger.error(f"Error getting quote for {symbol}: {str(e)}")
            return {}
    
    def get_technical_indicators(self, symbol: str, indicator: str, 
                               start_date: str, end_date: str) -> Dict[str, Any]:
        """Get technical indicators - Note: Limited support in Polygon.io API."""
        self._wait_for_rate_limit()
        
        try:
            # Polygon.io has limited technical indicators support
            # For now, return a placeholder response
            logger.warning(f"Technical indicators not fully supported in Polygon.io API for {symbol}")
            return {
                "s": "no_data",
                indicator: []
            }
            
        except Exception as e:
            logger.error(f"Error getting technical indicators for {symbol}: {str(e)}")
            return {"s": "error"}
    
    def get_reported_financials(self, symbol: str, freq: str = "annual") -> List[Dict[str, Any]]:
        """Get historical reported financials with processed financial data and derived metrics."""
        
        try:
            # Default to one year ago from today
            one_year_ago = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            
            # Get financial data using the vX endpoint
            financials = list(self._execute_with_retry(
                self.client.vx.list_stock_financials,
                ticker=symbol,
                period_of_report_date_gte=one_year_ago,
                limit=20
            ))
            
            # Filter by frequency and process financial data
            processed_financials = []
            for financial in financials:
                fiscal_quarter = getattr(financial, 'fiscal_quarter', None)
                
                # Filter by frequency
                if freq == "annual" and fiscal_quarter is not None:
                    continue
                elif freq == "quarterly" and fiscal_quarter is None:
                    continue
                
                # Convert Financials object to dictionary with derived metrics
                financials_obj = getattr(financial, 'financials', None)
                financials_dict = self._convert_financials_to_dict(financials_obj) if financials_obj else {}
                
                # Build comprehensive financial data structure
                financial_data = {
                    "cik": getattr(financial, 'cik', None),
                    "company_name": getattr(financial, 'company_name', None),
                    "end_date": getattr(financial, 'end_date', None),
                    "filing_date": getattr(financial, 'filing_date', None),
                    "fiscal_period": getattr(financial, 'fiscal_period', None),
                    "fiscal_year": getattr(financial, 'fiscal_year', None),
                    "start_date": getattr(financial, 'start_date', None),
                    "period_of_report_date": getattr(financial, 'period_of_report_date', None),
                    "source_filing_url": getattr(financial, 'source_filing_url', None),
                    "source_filing_file_url": getattr(financial, 'source_filing_file_url', None),
                    "financials": financials_dict  # Processed financial data with derived metrics
                }
                
                # Convert date objects to strings if necessary
                for date_field in ["end_date", "filing_date", "start_date", "period_of_report_date"]:
                    date_value = financial_data.get(date_field)
                    if date_value and hasattr(date_value, 'strftime'):
                        try:
                            financial_data[date_field] = date_value.strftime("%Y-%m-%d")
                        except:
                            financial_data[date_field] = str(date_value)
                
                processed_financials.append(financial_data)
            
            # Sort by period date (most recent first)
            processed_financials.sort(
                key=lambda x: x.get('period_of_report_date', '') or '', 
                reverse=True
            )
            
            return processed_financials
            
        except Exception as e:
            logger.error(f"Error getting reported financials for {symbol}: {str(e)}")
            return []
    
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
    
    def get_raw_reported_financials(self, symbol: str, period: str = "ttm") -> Dict[str, Any]:
        """Get raw reported financials directly from Polygon reference/financials endpoint."""
        try:
            # Use reference/financials endpoint for raw data
            from_date = (datetime.now() - timedelta(days=365*3)).strftime("%Y-%m-%d")  # 3 years
            
            # Get raw financials using reference endpoint
            # Note: This would require using the raw REST API, not the Python SDK
            # For now, return the processed data we already have
            financials = list(self._execute_with_retry(
                self.client.vx.list_stock_financials,
                ticker=symbol,
                period_of_report_date_gte=from_date,
                limit=20
            ))
            
            # Build response in Polygon reference/financials format
            results = []
            for financial in financials:
                result = {
                    "start_date": getattr(financial, 'start_date', ''),
                    "end_date": getattr(financial, 'end_date', ''),
                    "filing_date": getattr(financial, 'filing_date', ''),
                    "timeframe": getattr(financial, 'fiscal_period', '').lower() if hasattr(financial, 'fiscal_period') else '',
                    "fiscal_period": getattr(financial, 'fiscal_period', ''),
                    "fiscal_year": getattr(financial, 'fiscal_year', ''),
                    "cik": getattr(financial, 'cik', ''),
                    "company_name": getattr(financial, 'company_name', ''),
                    "financials": {}
                }
                
                # Convert processed financials back to raw format
                financials_obj = getattr(financial, 'financials', None)
                if financials_obj:
                    result["financials"] = self._convert_to_reference_format(financials_obj)
                
                # Convert dates to strings
                for date_field in ["start_date", "end_date", "filing_date"]:
                    date_value = result.get(date_field)
                    if date_value and hasattr(date_value, 'strftime'):
                        try:
                            result[date_field] = date_value.strftime("%Y-%m-%d")
                        except:
                            result[date_field] = str(date_value)
                
                results.append(result)
            
            return {
                "results": results,
                "status": "OK"
            }
            
        except Exception as e:
            logger.error(f"Error getting raw reported financials for {symbol}: {str(e)}")
            return {"results": [], "status": "ERROR"}
    
    def _convert_to_reference_format(self, financials_obj) -> Dict[str, Any]:
        """Convert processed financials back to reference format."""
        reference_format = {
            "balance_sheet": {},
            "income_statement": {},
            "cash_flow_statement": {},
            "comprehensive_income": {}
        }
        
        if not financials_obj:
            return reference_format
        
        # Process each financial statement section
        sections = ['balance_sheet', 'income_statement', 'cash_flow_statement', 'comprehensive_income']
        
        for section_name in sections:
            section_obj = getattr(financials_obj, section_name, None)
            if section_obj:
                # Get all attributes of the section object
                for attr_name in dir(section_obj):
                    if not attr_name.startswith('_'):  # Skip private attributes
                        attr_value = getattr(section_obj, attr_name, None)
                        
                        # Try to extract value from DataPoint
                        extracted_value = self._extract_datapoint_value(attr_value)
                        if extracted_value is not None:
                            # Create reference format entry
                            reference_format[section_name][attr_name] = {
                                "value": extracted_value,
                                "unit": "USD",
                                "label": attr_name.replace('_', ' ').title(),
                                "order": 100
                            }
        
        return reference_format

    def search_tickers(self, query: str, limit: int = 20, active: bool = True) -> List[Dict[str, Any]]:
        """Search for tickers by symbol or company name using Polygon.io Reference API."""
        try:
            response = self._execute_with_retry(
                self.client.get_tickers,
                search=query,
                active=active,
                limit=limit
            )
            results = response.get('results', [])
            # Return a simplified list of tickers
            return [
                {
                    'symbol': t.get('ticker'),
                    'name': t.get('name'),
                    'market': t.get('market'),
                    'locale': t.get('locale'),
                    'primary_exchange': t.get('primary_exchange'),
                    'currency_name': t.get('currency_name'),
                    'active': t.get('active'),
                    'type': t.get('type'),
                }
                for t in results
            ]
        except Exception as e:
            logger.error(f"Error searching tickers for query '{query}': {str(e)}")
            return [] 