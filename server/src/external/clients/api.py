import datetime
import pandas as pd
import logging
from typing import Optional, List
from datetime import datetime, timedelta

from src.data.cache import get_cache
from src.data.models import (
    CompanyNews,
    FinancialMetrics,
    Price,
    LineItem,
    InsiderTrade,
    LineItemName,
    FinancialPeriod,
    SentimentType,
)
from src.external.clients.polygon_client import PolygonClient
from src.external.clients.alpaca_client import AlpacaClient
from src.external.clients.financial_calculator import FinancialCalculator
from src.external.clients.field_adapters import FieldMappingService, PolygonFieldMappingService


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


_cache = get_cache()


polygon_client = PolygonClient()
alpaca_client = AlpacaClient()
financial_calculator = FinancialCalculator()
field_mapping_service = FieldMappingService()
polygon_field_mapping_service = PolygonFieldMappingService()

def get_prices(ticker: str, start_date: str, end_date: str) -> List[Price]:
    """Fetch price data from cache or Alpaca API."""
    
    if cached_data := _cache.get_prices(ticker):
        
        filtered_data = [Price(**price) for price in cached_data if start_date <= price["time"] <= end_date]
        if filtered_data:
            return filtered_data

    try:
        
        data = alpaca_client.get_stock_price(ticker, start_date, end_date)

        if data["s"] != "ok":
            raise Exception(f"Error fetching data: {ticker} - {data['s']}")

        
        prices = []
        for i in range(len(data["t"])):
            prices.append(Price(
                time=datetime.fromtimestamp(data["t"][i]).strftime("%Y-%m-%d"),
                open=data["o"][i],
                high=data["h"][i],
                low=data["l"][i],
                close=data["c"][i],
                volume=data["v"][i]
            ))

        if not prices:
            return []

        
        _cache.set_prices(ticker, [p.model_dump() for p in prices])
        return prices

    except Exception as e:
        logger.error(f"Error fetching prices for {ticker}: {str(e)}")
        raise

def get_financial_metrics(
    ticker: str,
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
) -> List[FinancialMetrics]:
    """Fetch financial metrics from cache or Polygon API using definitive adapter."""
    
    if cached_data := _cache.get_financial_metrics(ticker):
        filtered_data = [FinancialMetrics(**metric) for metric in cached_data
                        if metric["report_period"] <= end_date and metric.get("period", "ttm") == period]
        filtered_data.sort(key=lambda x: x.report_period, reverse=True)
        if filtered_data:
            return filtered_data[:limit]

    try:
        from src.external.clients.field_adapters import PolygonFinancialAdapter
        
        # Get company profile for market cap and currency
        profile = polygon_client.get_company_profile(ticker)
        
        # Get raw reported financials using new endpoint
        raw_financials = polygon_client.get_raw_reported_financials(ticker, period=period)
        
        # Initialize adapter
        adapter = PolygonFinancialAdapter()
        
        # Extract structured financial data
        financial_data_list = adapter.extract_financial_data(raw_financials)
        
        if not financial_data_list:
            logger.warning(f"No financial data available for {ticker}")
            return []
        
        result = []
        market_cap = profile.get("marketCapitalization")
        
        # Process each financial period
        for data in financial_data_list[:limit]:
            # Calculate all financial metrics
            calculated_metrics = adapter.calculate_financial_metrics(data, market_cap)
            
            # Determine report period
            report_period = data.period or end_date
            
            # Create FinancialMetrics object
            metrics = FinancialMetrics(
                ticker=ticker,
                report_period=report_period,
                period=period,
                currency=profile.get("currency", "USD"),
                
                # Market & Valuation
                market_cap=calculated_metrics.get("market_cap"),
                enterprise_value=None,  # Not calculated in basic adapter
                price_to_earnings_ratio=None,  # Requires stock price
                price_to_book_ratio=None,  # Requires stock price  
                price_to_sales_ratio=None,  # Requires stock price
                enterprise_value_to_ebitda_ratio=None,  # Requires enterprise value
                enterprise_value_to_revenue_ratio=None,  # Requires enterprise value
                free_cash_flow_yield=None,  # Requires market cap and FCF
                peg_ratio=None,  # Requires P/E and growth rate
                
                # Profitability & Margins
                gross_margin=calculated_metrics.get("gross_margin"),
                operating_margin=calculated_metrics.get("operating_margin"),
                net_margin=calculated_metrics.get("net_margin"),
                return_on_equity=calculated_metrics.get("return_on_equity"),
                return_on_assets=calculated_metrics.get("return_on_assets"),
                return_on_invested_capital=None,  # Requires ROIC calculation
                
                # Activity & Efficiency
                asset_turnover=calculated_metrics.get("asset_turnover"),
                inventory_turnover=calculated_metrics.get("inventory_turnover"),
                receivables_turnover=calculated_metrics.get("receivables_turnover"),
                days_sales_outstanding=calculated_metrics.get("days_sales_outstanding"),
                operating_cycle=None,  # Could be calculated
                working_capital_turnover=None,  # Could be calculated
                
                # Liquidity
                current_ratio=calculated_metrics.get("current_ratio"),
                quick_ratio=None,  # Requires quick assets calculation
                cash_ratio=None,  # Could be calculated
                operating_cash_flow_ratio=calculated_metrics.get("operating_cash_flow_ratio"),
                
                # Leverage
                debt_to_equity=calculated_metrics.get("debt_to_equity"),
                debt_to_assets=calculated_metrics.get("debt_to_assets"),
                interest_coverage=None,  # Requires EBIT/Interest calculation
                
                # Growth - Not available from single period data
                revenue_growth=None,
                earnings_growth=None,
                book_value_growth=None,
                earnings_per_share_growth=None,
                free_cash_flow_growth=None,
                operating_income_growth=None,
                ebitda_growth=None,
                
                # Per Share
                earnings_per_share=calculated_metrics.get("earnings_per_share"),
                book_value_per_share=calculated_metrics.get("book_value_per_share"),
                free_cash_flow_per_share=calculated_metrics.get("free_cash_flow_per_share"),
                payout_ratio=None  # Requires dividends data
            )
            
            result.append(metrics)
        
        # Cache and return results
        _cache.set_financial_metrics(ticker, [m.model_dump() for m in result])
        return result[:limit]
        
    except Exception as e:
        logger.error(f"Error fetching financial metrics for {ticker}: {str(e)}")
        raise




def get_insider_trades(
    ticker: str,
    end_date: str,
    start_date: Optional[str] = None,
    limit: int = 1000,
) -> List[InsiderTrade]:
    """Insider trades are not supported in this implementation."""
    logger.info(f"Insider trades functionality has been removed from the algorithm")
    return []

def get_company_news(
    ticker: str,
    end_date: str,
    start_date: Optional[str] = None,
    limit: int = 1000,
) -> List[CompanyNews]:
    """Fetch company news from cache or FinnHub API."""
    
    if cached_data := _cache.get_company_news(ticker):
        filtered_data = [CompanyNews(**news) for news in cached_data
                        if (start_date is None or news["date"] >= start_date)
                        and news["date"] <= end_date]
        filtered_data.sort(key=lambda x: x.date, reverse=True)
        if filtered_data:
            return filtered_data[:limit]  # Apply limit to cached data too

    try:
        
        data = polygon_client.get_company_news(ticker, start_date or "2025-01-01", end_date, limit=limit)

        
        news_items = []
        for item in data:
            
            date = datetime.fromtimestamp(item.get("datetime", 0)).strftime("%Y-%m-%d")

            news_items.append(CompanyNews(
                ticker=ticker,
                title=item.get("headline", ""),
                author="",  
                source=item.get("source", ""),
                date=date,
                url=item.get("url", ""),
                sentiment=item.get("sentiment", SentimentType.NEUTRAL)  # Now returns SentimentType enum
            ))

        if not news_items:
            return []

        
        _cache.set_company_news(ticker, [news.model_dump() for news in news_items])
        return news_items

    except Exception as e:
        logger.error(f"Error fetching company news for {ticker}: {str(e)}")
        raise

def get_market_cap(ticker: str, end_date: str) -> Optional[float]:
    """Fetch market cap from FinnHub API."""
    try:
        
        quote = polygon_client.get_quote(ticker)
        return quote.get("marketCap")
    except Exception as e:
        logger.error(f"Error fetching market cap for {ticker}: {str(e)}")
        return None

def prices_to_df(prices: List[Price]) -> pd.DataFrame:
    """Convert prices to a DataFrame."""
    df = pd.DataFrame([p.model_dump() for p in prices])
    df["Date"] = pd.to_datetime(df["time"])
    df.set_index("Date", inplace=True)
    numeric_cols = ["open", "close", "high", "low", "volume"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.sort_index(inplace=True)
    return df

def get_price_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Get price data as DataFrame."""
    prices = get_prices(ticker, start_date, end_date)
    return prices_to_df(prices)

def search_line_items(
    ticker: str,
    line_items: List[LineItemName],
    end_date: str,
    period: FinancialPeriod = FinancialPeriod.TTM,
    limit: int = 1000
) -> List[LineItem]:
    """Search for specific line items using definitive adapter mappings."""
    
    # Check cache first
    period_str = period.value if hasattr(period, 'value') else str(period).lower()
    if cached_data := _cache.get_line_items(ticker):
        filtered_data = [LineItem(**item) for item in cached_data
                        if item["report_period"] <= end_date and item.get("period", "ttm") == period_str]
        filtered_data.sort(key=lambda x: x.report_period, reverse=True)
        if filtered_data:
            return filtered_data[:limit]

    try:
        from src.external.clients.field_adapters import PolygonFinancialAdapter
        
        logger.info(f"Searching line items for {ticker}: {[item.value if hasattr(item, 'value') else str(item) for item in line_items]}")
        
        # Get company profile for additional context
        profile = polygon_client.get_company_profile(ticker)
        
        # Get raw reported financials
        raw_financials = polygon_client.get_raw_reported_financials(ticker, period=period_str)
        
        # Initialize adapter
        adapter = PolygonFinancialAdapter()
        
        # Extract structured financial data
        financial_data_list = adapter.extract_financial_data(raw_financials)
        
        if not financial_data_list:
            logger.warning(f"No financial data available for {ticker}")
            return []
        
        result = []
        
        # Process each financial period
        for financial_data in financial_data_list[:limit]:
            # Get the definitive field mappings for this data period
            field_mappings = adapter.get_line_item_mappings(financial_data)
            
            # Determine report period
            report_period = financial_data.period or end_date
            
            # Process each requested line item
            for line_item in line_items:
                # Handle both enum and string inputs
                if hasattr(line_item, 'value'):
                    line_item_str = line_item.value
                else:
                    line_item_str = str(line_item)
                
                # Get the value using definitive adapter mapping
                value = field_mappings.get(line_item_str)
                
                if value is not None:
                    result.append(LineItem(
                        ticker=ticker,
                        name=line_item_str,
                        value=float(value),
                        report_period=report_period,
                        period=period_str,
                        currency=profile.get("currency", "USD"),
                        source="polygon_adapter"
                    ))
                    logger.info(f"Found {line_item_str}: {value} for period {report_period}")
                else:
                    logger.debug(f"No value found for {line_item_str} in period {report_period}")
        
        # Sort by report period (most recent first)
        result.sort(key=lambda x: x.report_period, reverse=True)
        
        # Cache results
        if result:
            _cache.set_line_items(ticker, [item.model_dump() for item in result])
        
        logger.info(f"Returning {len(result)} line items for {ticker}")
        return result[:limit]
        
    except Exception as e:
        logger.error(f"Error searching line items for {ticker}: {str(e)}")
        raise

 