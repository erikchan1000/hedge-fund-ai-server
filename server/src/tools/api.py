import datetime
import os
import pandas as pd
import logging
from typing import Optional, List
from datetime import datetime, timedelta

from data.cache import get_cache
from data.models import (
    CompanyNews,
    FinancialMetrics,
    Price,
    LineItem,
    InsiderTrade
)
from .finnhub_client import FinnHubClient
from .alpaca_client import AlpacaClient
from .finnhub_adapters import map_finnhub_metric_to_financial_metrics

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Global cache instance
_cache = get_cache()

# Initialize clients
finnhub_client = FinnHubClient()
alpaca_client = AlpacaClient()

def get_prices(ticker: str, start_date: str, end_date: str) -> List[Price]:
    """Fetch price data from cache or Alpaca API."""
    # Check cache first
    if cached_data := _cache.get_prices(ticker):
        # Filter cached data by date range and convert to Price objects
        filtered_data = [Price(**price) for price in cached_data if start_date <= price["time"] <= end_date]
        if filtered_data:
            return filtered_data

    try:
        # Fetch from Alpaca
        data = alpaca_client.get_stock_price(ticker, start_date, end_date)
        
        if data["s"] != "ok":
            raise Exception(f"Error fetching data: {ticker} - {data['s']}")

        # Convert to our Price model
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

        # Cache the results
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
    """Fetch financial metrics from cache or FinnHub API."""
    # Check cache first
    if cached_data := _cache.get_financial_metrics(ticker):
        filtered_data = [FinancialMetrics(**metric) for metric in cached_data 
                        if metric["report_period"] <= end_date]
        filtered_data.sort(key=lambda x: x.report_period, reverse=True)
        if filtered_data:
            return filtered_data[:limit]

    try:
        # Get company profile for basic info
        profile = finnhub_client.get_company_profile(ticker)
        
        # Get financial metrics using the metric endpoint (this contains the actual financial data)
        metrics_data = finnhub_client.get_basic_financials(ticker)
        
        # Use the adapter to map Finnhub response to FinancialMetrics
        metrics = map_finnhub_metric_to_financial_metrics(
            ticker,
            metrics_data,
            end_date,
            period,
            profile.get("currency", "USD")
        )

        # Cache the results
        _cache.set_financial_metrics(ticker, [metrics.model_dump()])
        return [metrics]

    except Exception as e:
        logger.error(f"Error fetching financial metrics for {ticker}: {str(e)}")
        raise

def get_insider_trades(
    ticker: str,
    end_date: str,
    start_date: Optional[str] = None,
    limit: int = 1000,
) -> List[InsiderTrade]:
    """Fetch insider trades from cache or FinnHub API."""
    # Check cache first
    if cached_data := _cache.get_insider_trades(ticker):
        filtered_data = [InsiderTrade(**trade) for trade in cached_data 
                        if (start_date is None or trade["transaction_date"] >= start_date)
                        and trade["transaction_date"] <= end_date]
        filtered_data.sort(key=lambda x: x.transaction_date, reverse=True)
        if filtered_data:
            return filtered_data

    try:
        # Fetch from FinnHub
        data = finnhub_client.get_insider_transactions(ticker)
        
        # Convert to our InsiderTrade model
        trades = []
        for trade in data.get("data", []):
            # Map FinnHub fields to our model
            transaction_type = "buy" if trade.get("change") > 0 else "sell"
            shares = abs(trade.get("change", 0))
            price_per_share = trade.get("price", 0)
            total_value = shares * price_per_share
            
            trades.append(InsiderTrade(
                ticker=ticker,
                issuer=ticker,  # Using ticker as issuer since FinnHub doesn't provide this
                name=trade.get("name", ""),
                title=trade.get("title", ""),
                is_board_director=None,  # FinnHub doesn't provide this information
                transaction_date=trade.get("transactionDate", ""),
                transaction_shares=shares,
                transaction_price_per_share=price_per_share,
                transaction_value=total_value,
                shares_owned_before_transaction=None,  # FinnHub doesn't provide this
                shares_owned_after_transaction=None,  # FinnHub doesn't provide this
                security_title="Common Stock",  # Default to common stock since FinnHub doesn't provide this
                filing_date=trade.get("filingDate", "")
            ))

        if not trades:
            return []

        # Cache the results
        _cache.set_insider_trades(ticker, [trade.model_dump() for trade in trades])
        return trades

    except Exception as e:
        logger.error(f"Error fetching insider trades for {ticker}: {str(e)}")
        raise

def get_company_news(
    ticker: str,
    end_date: str,
    start_date: Optional[str] = None,
    limit: int = 1000,
) -> List[CompanyNews]:
    """Fetch company news from cache or FinnHub API."""
    # Check cache first
    if cached_data := _cache.get_company_news(ticker):
        filtered_data = [CompanyNews(**news) for news in cached_data 
                        if (start_date is None or news["date"] >= start_date)
                        and news["date"] <= end_date]
        filtered_data.sort(key=lambda x: x.date, reverse=True)
        if filtered_data:
            return filtered_data

    try:
        # Fetch from FinnHub
        data = finnhub_client.get_company_news(ticker, start_date or "2020-01-01", end_date)
        
        # Convert to our CompanyNews model
        news_items = []
        for item in data:
            # Convert timestamp to date string
            date = datetime.fromtimestamp(item.get("datetime", 0)).strftime("%Y-%m-%d")
            
            news_items.append(CompanyNews(
                ticker=ticker,
                title=item.get("headline", ""),
                author="",  # FinnHub doesn't provide author information
                source=item.get("source", ""),
                date=date,
                url=item.get("url", ""),
                sentiment=str(item.get("sentiment", 0))  # Convert to string as required by model
            ))

        if not news_items:
            return []

        # Cache the results
        _cache.set_company_news(ticker, [news.model_dump() for news in news_items])
        return news_items

    except Exception as e:
        logger.error(f"Error fetching company news for {ticker}: {str(e)}")
        raise

def get_market_cap(ticker: str, end_date: str) -> Optional[float]:
    """Fetch market cap from FinnHub API."""
    try:
        # Get quote data which includes market cap
        quote = finnhub_client.get_quote(ticker)
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

def search_line_items(ticker: str, line_items: List[str], end_date: str) -> List[LineItem]:
    """Fetch specific financial line items from FinnHub API."""
    try:
        # Get financial metrics using the metric endpoint
        metrics_data = finnhub_client.get_basic_financials(ticker)
        metric = metrics_data.get("metric", {})
        series = metrics_data.get("series", {})
        
        # Map line items to FinnHub metric fields (corrected mappings based on actual API response)
        line_item_map = {
            "earnings_per_share": "epsBasicExclExtraItemsTTM",
            "revenue": "revenuePerShareTTM",  # Updated to available field
            "net_income": "netProfitMarginTTM",  # Using margin since absolute values not available
            "book_value_per_share": "bookValuePerShareAnnual",
            "total_assets": None,  # totalAssetsAnnual not available in API response
            "total_liabilities": None,  # totalLiabilitiesAnnual not available in API response
            "current_assets": None,  # currentAssetsAnnual not available in API response
            "current_liabilities": None,  # currentLiabilitiesAnnual not available in API response
            "operating_cash_flow": "cashFlowPerShareTTM",  # Using cash flow per share
            "free_cash_flow": None,  # freeCashFlowTTM not available in API response
            "gross_profit": "grossMarginTTM",  # Using margin since absolute values not available
            "operating_income": "operatingMarginTTM",  # Using margin since absolute values not available
            "interest_expense": None,  # interestExpenseTTM not available in API response
            "total_debt": None,  # totalDebtAnnual not available in API response
            "cash_and_equivalents": "cashPerSharePerShareAnnual",  # Using cash per share
            "inventory": None,  # inventoryAnnual not available in API response
            "accounts_receivable": None,  # accountsReceivableAnnual not available in API response
            "long_term_debt": "longTermDebt/equityAnnual",  # Using debt ratio instead
            "short_term_debt": None,  # shortTermDebtAnnual not available in API response
            "capital_expenditures": None,  # capitalExpenditureTTM not available in API response
            "dividends_and_other_cash": "dividendPerShareTTM",  # Using dividend per share
            "depreciation_and_amortization": None,  # depreciationAmortizationTTM not available in API response
            "research_and_development": None,  # researchNDevelopmentExpenseTTM not available in API response
            "selling_general_and_administrative": None,  # sellGeneralAdminExpenseTotalTTM not available in API response
        }
        
        # Convert to LineItem objects
        result = []
        for item in line_items:
            if item in line_item_map and line_item_map[item] is not None:
                finnhub_field = line_item_map[item]
                value = metric.get(finnhub_field)
                
                # If not in metric, try to get from series data
                if value is None and series:
                    # For series data, look for annual data
                    annual_series = series.get("annual", {})
                    if annual_series and isinstance(annual_series, dict):
                        series_data = annual_series.get(finnhub_field, [])
                        if series_data and isinstance(series_data, list) and len(series_data) > 0:
                            # Get the most recent period value
                            recent_data = series_data[-1]
                            value = recent_data.get("v") if isinstance(recent_data, dict) else recent_data
                
                if value is not None:
                    # Ensure value is numeric
                    try:
                        numeric_value = float(value) if value is not None else None
                        if numeric_value is not None:
                            result.append(LineItem(
                                name=item,
                                value=numeric_value,
                                report_period=end_date
                            ))
                    except (ValueError, TypeError):
                        logger.warning(f"Could not convert value {value} to float for {item}")
                        continue
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching line items for {ticker}: {str(e)}")
        raise