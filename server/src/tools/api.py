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
    InsiderTrade,
    )

from .finnhub_client import FinnHubClient
from .alpaca_client import AlpacaClient

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
        # Get company profile for basic metrics
        profile = finnhub_client.get_company_profile(ticker)

        # Get financial statements
        income = finnhub_client.get_financial_statements(ticker, "income")
        balance = finnhub_client.get_financial_statements(ticker, "balance")
        cash_flow = finnhub_client.get_financial_statements(ticker, "cash")
        print("Debug profile", profile, income, balance, cash_flow)

        # Convert to our FinancialMetrics model
        metrics = FinancialMetrics(
            report_period=end_date,
            market_cap=profile.get("marketCapitalization"),
            pe_ratio=profile.get("pe"),
            pb_ratio=profile.get("pb"),
            ps_ratio=profile.get("ps"),
            # Add more metrics as needed
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
        # Get financial statements from FinnHub
        income = finnhub_client.get_financial_statements(ticker, "income")
        balance = finnhub_client.get_financial_statements(ticker, "balance")
        cash_flow = finnhub_client.get_financial_statements(ticker, "cash")

        # Map line items to FinnHub fields
        line_item_map = {
            "earnings_per_share": "basicEps",
            "revenue": "totalRevenue",
            "net_income": "netIncome",
            "book_value_per_share": "bookValuePerShare",
            "total_assets": "totalAssets",
            "total_liabilities": "totalLiabilities",
            "current_assets": "totalCurrentAssets",
            "current_liabilities": "totalCurrentLiabilities",
            "dividends_and_other_cash": "dividendsPaid",
            "operating_cash_flow": "operatingCashFlow",
            "free_cash_flow": "freeCashFlow",
            "gross_profit": "grossProfit",
            "operating_income": "operatingIncome",
            "interest_expense": "interestExpense",
            "depreciation_and_amortization": "depreciationAndAmortization",
            "research_and_development": "researchAndDevelopment",
            "selling_general_and_administrative": "sellingGeneralAndAdministrative",
            "total_debt": "totalDebt",
            "cash_and_equivalents": "cashAndCashEquivalents",
            "inventory": "inventory",
            "accounts_receivable": "netReceivables",
            "accounts_payable": "accountsPayable",
            "long_term_debt": "longTermDebt",
            "short_term_debt": "shortTermDebt",
            "capital_expenditures": "capitalExpenditure",
            "net_cash_flow": "netCashFlow",
            "net_cash_flow_from_operating_activities": "netCashFlowFromOperatingActivities",
            "net_cash_flow_from_investing_activities": "netCashFlowFromInvestingActivities",
            "net_cash_flow_from_financing_activities": "netCashFlowFromFinancingActivities",
            "net_cash_flow_from_discontinued_operations": "netCashFlowFromDiscontinuedOperations",
            "net_cash_flow_from_continuing_operations": "netCashFlowFromContinuingOperations",
            "net_cash_flow_from_operating_activities_continuing_operations": "netCashFlowFromOperatingActivitiesContinuingOperations",
            "net_cash_flow_from_investing_activities_continuing_operations": "netCashFlowFromInvestingActivitiesContinuingOperations",
            "net_cash_flow_from_financing_activities_continuing_operations": "netCashFlowFromFinancingActivitiesContinuingOperations",
            "net_cash_flow_from_discontinued_operations_continuing_operations": "netCashFlowFromDiscontinuedOperationsContinuingOperations",
            "net_cash_flow_from_continuing_operations_continuing_operations": "netCashFlowFromContinuingOperationsContinuingOperations",
            "net_cash_flow_from_operating_activities_discontinued_operations": "netCashFlowFromOperatingActivitiesDiscontinuedOperations",
            "net_cash_flow_from_investing_activities_discontinued_operations": "netCashFlowFromInvestingActivitiesDiscontinuedOperations",
            "net_cash_flow_from_financing_activities_discontinued_operations": "netCashFlowFromFinancingActivitiesDiscontinuedOperations",
            "net_cash_flow_from_discontinued_operations_discontinued_operations": "netCashFlowFromDiscontinuedOperationsDiscontinuedOperations",
            "net_cash_flow_from_continuing_operations_discontinued_operations": "netCashFlowFromContinuingOperationsDiscontinuedOperations",
            "net_cash_flow_from_operating_activities_continuing_operations_discontinued_operations": "netCashFlowFromOperatingActivitiesContinuingOperationsDiscontinuedOperations",
            "net_cash_flow_from_investing_activities_continuing_operations_discontinued_operations": "netCashFlowFromInvestingActivitiesContinuingOperationsDiscontinuedOperations",
            "net_cash_flow_from_financing_activities_continuing_operations_discontinued_operations": "netCashFlowFromFinancingActivitiesContinuingOperationsDiscontinuedOperations",
            "net_cash_flow_from_discontinued_operations_continuing_operations_discontinued_operations": "netCashFlowFromDiscontinuedOperationsContinuingOperationsDiscontinuedOperations",
            "net_cash_flow_from_continuing_operations_continuing_operations_discontinued_operations": "netCashFlowFromContinuingOperationsContinuingOperationsDiscontinuedOperations",
        }

        # Convert to LineItem objects
        result = []
        for item in line_items:
            if item in line_item_map:
                finnhub_field = line_item_map[item]
                value = None

                # Search in income statement
                if finnhub_field in income:
                    value = income[finnhub_field]
                # Search in balance sheet
                elif finnhub_field in balance:
                    value = balance[finnhub_field]
                # Search in cash flow statement
                elif finnhub_field in cash_flow:
                    value = cash_flow[finnhub_field]

                if value is not None:
                    result.append(LineItem(
                        name=item,
                        value=value,
                        report_period=end_date
                    ))

        return result

    except Exception as e:
        logger.error(f"Error fetching line items for {ticker}: {str(e)}")
        raise
