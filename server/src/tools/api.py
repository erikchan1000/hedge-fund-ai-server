import datetime
import os
import pandas as pd
import logging
from typing import Optional, List
from datetime import datetime, timedelta

from data.cache import get_cache
from data.models import (
    CompanyNews,
    CompanyNewsResponse,
    FinancialMetrics,
    FinancialMetricsResponse,
    Price,
    PriceResponse,
    LineItem,
    LineItemResponse,
    InsiderTrade,
    InsiderTradeResponse,
    CompanyFactsResponse,
)
from .finnhub_client import FinnHubClient
from .alpaca_client import AlpacaClient
from .financial_calculator import FinancialCalculator
from .field_adapters import FieldMappingService


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


_cache = get_cache()


finnhub_client = FinnHubClient()
alpaca_client = AlpacaClient()
financial_calculator = FinancialCalculator()
field_mapping_service = FieldMappingService()

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
    """Fetch financial metrics from cache or FinnHub API."""
    
    if cached_data := _cache.get_financial_metrics(ticker):
        filtered_data = [FinancialMetrics(**metric) for metric in cached_data
                        if metric["report_period"] <= end_date and metric.get("period", "ttm") == period]
        filtered_data.sort(key=lambda x: x.report_period, reverse=True)
        if filtered_data:
            return filtered_data[:limit]

    try:
        
        profile = finnhub_client.get_company_profile(ticker)

        
        metrics_data = finnhub_client.get_basic_financials(ticker, period=period, limit=limit)

        
        metric = metrics_data.get("metric", {})
        series = metrics_data.get("series", {})

        
        logger.info(f"Retrieved {len(metric)} metrics and {len(series)} series for {ticker}")

        
        if series:
            logger.info(f"Available series for {ticker}:")
            for series_type, series_data in series.items():
                if isinstance(series_data, dict):
                    logger.info(f"  {series_type}: {len(series_data)} series - {list(series_data.keys())[:5]}...")
                else:
                    logger.info(f"  {series_type}: {type(series_data)}")

        
        if period.lower() == "ttm":
            suffix = "TTM"
            series_key = "quarterly"  
        elif period.lower() in ["annual", "yearly"]:
            suffix = "Annual"
            series_key = "annual"
        else:
            suffix = "TTM"  
            series_key = "quarterly"

        
        market_cap = metric.get("marketCapitalization")
        enterprise_value = metric.get("enterpriseValue")

        
        pe_ratio = metric.get(f"peBasicExclExtra{suffix}")
        earnings_growth = metric.get(f"epsGrowth{suffix}Yoy") if suffix == "TTM" else metric.get("epsGrowthTTMYoy")
        receivables_turnover = metric.get(f"receivablesTurnover{suffix}")
        inventory_turnover = metric.get(f"inventoryTurnover{suffix}")
        current_ratio = metric.get(f"currentRatio{suffix}")
        quick_ratio = metric.get(f"quickRatio{suffix}")
        debt_to_equity = metric.get(f"totalDebt/totalEquity{suffix}")
        revenue_per_share = metric.get(f"revenuePerShare{suffix}")
        cash_per_share = metric.get(f"cashPerSharePerShare{suffix}")
        book_value_per_share = metric.get(f"bookValuePerShare{suffix}")

        
        ev_ebitda = metric.get(f"evEbitda{suffix}") or metric.get(f"enterpriseValueEbitda{suffix}")
        ev_revenue = metric.get(f"evRevenue{suffix}") or metric.get(f"enterpriseValueRevenue{suffix}")
        free_cash_flow = metric.get(f"freeCashFlow{suffix}") if suffix == "TTM" else metric.get("freeCashFlowTTM")
        total_debt = metric.get(f"totalDebt{suffix}")
        total_assets = metric.get(f"totalAssets{suffix}")
        current_assets = metric.get(f"currentAssets{suffix}")
        current_liabilities = metric.get(f"currentLiabilities{suffix}")
        cash_and_equivalents = metric.get(f"cashAndEquivalents{suffix}")
        operating_cash_flow = metric.get(f"operatingCashFlow{suffix}") if suffix == "TTM" else metric.get("operatingCashFlowTTM")
        shares_outstanding = profile.get("shareOutstanding")

        
        
        enterprise_value_to_ebitda_ratio = ev_ebitda
        if not enterprise_value_to_ebitda_ratio and enterprise_value:
            ebitda_field = f"ebitda{suffix}"
            if metric.get(ebitda_field):
                enterprise_value_to_ebitda_ratio = enterprise_value / metric.get(ebitda_field)

        
        enterprise_value_to_revenue_ratio = ev_revenue
        if not enterprise_value_to_revenue_ratio and enterprise_value and revenue_per_share and shares_outstanding:
            revenue = revenue_per_share * shares_outstanding
            if revenue > 0:
                enterprise_value_to_revenue_ratio = enterprise_value / revenue

        
        free_cash_flow_yield = None
        if free_cash_flow and market_cap and market_cap > 0:
            free_cash_flow_yield = free_cash_flow / market_cap

        
        peg_ratio = None
        if pe_ratio and earnings_growth and earnings_growth > 0:
            
            growth_rate = earnings_growth / 100 if earnings_growth > 1 else earnings_growth
            if growth_rate > 0:
                peg_ratio = pe_ratio / (growth_rate * 100)

        
        days_sales_outstanding = None
        if receivables_turnover and receivables_turnover > 0:
            days_sales_outstanding = 365 / receivables_turnover

        
        operating_cycle = None
        if days_sales_outstanding and inventory_turnover and inventory_turnover > 0:
            days_inventory_outstanding = 365 / inventory_turnover
            operating_cycle = days_sales_outstanding + days_inventory_outstanding

        
        working_capital_turnover = None
        if revenue_per_share and shares_outstanding and current_assets and current_liabilities:
            revenue = revenue_per_share * shares_outstanding
            working_capital = current_assets - current_liabilities
            if working_capital > 0:
                working_capital_turnover = revenue / working_capital

        
        cash_ratio = None
        if cash_and_equivalents and current_liabilities and current_liabilities > 0:
            cash_ratio = cash_and_equivalents / current_liabilities
        elif cash_per_share and shares_outstanding and current_liabilities and current_liabilities > 0:
            total_cash = cash_per_share * shares_outstanding
            cash_ratio = total_cash / current_liabilities

        
        operating_cash_flow_ratio = None
        if operating_cash_flow and current_liabilities and current_liabilities > 0:
            operating_cash_flow_ratio = operating_cash_flow / current_liabilities

        
        debt_to_assets = None
        if total_debt and total_assets and total_assets > 0:
            debt_to_assets = total_debt / total_assets
        elif debt_to_equity and debt_to_equity > 0:
            
            debt_to_assets = debt_to_equity / (1 + debt_to_equity)

        
        free_cash_flow_per_share = None
        if free_cash_flow and shares_outstanding and shares_outstanding > 0:
            free_cash_flow_per_share = free_cash_flow / shares_outstanding

        
        growth_rates = calculate_growth_rates(ticker, [
            "revenue", "net_income", "free_cash_flow", "book_value",
            "ebitda", "operating_income", "earnings_per_share"
        ], periods=3, period=period)

        
        metrics = FinancialMetrics(
            ticker=ticker,
            report_period=end_date,
            period=period,
            currency=profile.get("currency", "USD"),
            market_cap=market_cap,
            enterprise_value=enterprise_value,
            price_to_earnings_ratio=pe_ratio,
            price_to_book_ratio=metric.get(f"pb{suffix}"),
            price_to_sales_ratio=metric.get(f"ps{suffix}"),
            enterprise_value_to_ebitda_ratio=enterprise_value_to_ebitda_ratio,
            enterprise_value_to_revenue_ratio=enterprise_value_to_revenue_ratio,
            free_cash_flow_yield=free_cash_flow_yield,
            peg_ratio=peg_ratio,
            gross_margin=metric.get(f"grossMargin{suffix}"),
            operating_margin=metric.get(f"operatingMargin{suffix}"),
            net_margin=metric.get(f"netProfitMargin{suffix}"),
            return_on_equity=metric.get(f"roe{suffix}"),
            return_on_assets=metric.get(f"roa{suffix}"),
            return_on_invested_capital=metric.get(f"roi{suffix}"),
            asset_turnover=metric.get(f"assetTurnover{suffix}"),
            inventory_turnover=inventory_turnover,
            receivables_turnover=receivables_turnover,
            days_sales_outstanding=days_sales_outstanding,
            operating_cycle=operating_cycle,
            working_capital_turnover=working_capital_turnover,
            current_ratio=current_ratio,
            quick_ratio=quick_ratio,
            cash_ratio=cash_ratio,
            operating_cash_flow_ratio=operating_cash_flow_ratio,
            debt_to_equity=debt_to_equity,
            debt_to_assets=debt_to_assets,
            interest_coverage=metric.get(f"netInterestCoverage{suffix}"),
            revenue_growth=metric.get(f"revenueGrowth{suffix}Yoy") or growth_rates.get("revenue_growth"),
            earnings_growth=earnings_growth or growth_rates.get("earnings_per_share_growth"),
            book_value_growth=growth_rates.get("book_value_growth"),
            earnings_per_share_growth=earnings_growth or growth_rates.get("earnings_per_share_growth"),
            free_cash_flow_growth=growth_rates.get("free_cash_flow_growth"),
            operating_income_growth=growth_rates.get("operating_income_growth"),
            ebitda_growth=growth_rates.get("ebitda_growth"),
            payout_ratio=metric.get(f"payoutRatio{suffix}"),
            earnings_per_share=metric.get(f"epsBasicExclExtraItems{suffix}"),
            book_value_per_share=book_value_per_share,
            free_cash_flow_per_share=free_cash_flow_per_share
        )

        
        result = [metrics]

        
        if limit > 1 and series:
            historical_periods = []
            series_data = series.get(series_key, {})

            if series_data and isinstance(series_data, dict):
                
                key_metrics = ["marketCapitalization", "epsBasicExclExtraItemsAnnual", "revenuePerShareAnnual"]

                for key_metric in key_metrics:
                    if key_metric in series_data:
                        historical_data = series_data[key_metric]
                        if isinstance(historical_data, list) and len(historical_data) > 1:
                            
                            sorted_data = sorted(historical_data, key=lambda x: x.get("period", ""), reverse=True)

                            
                            for i, period_data in enumerate(sorted_data[1:limit]):
                                if isinstance(period_data, dict) and period_data.get("period"):
                                    
                                    historical_metrics = FinancialMetrics(
                                        ticker=ticker,
                                        report_period=period_data["period"],
                                        period=period,
                                        currency=profile.get("currency", "USD"),
                                        market_cap=None,  
                                        enterprise_value=None,
                                        price_to_earnings_ratio=None,
                                        price_to_book_ratio=None,
                                        price_to_sales_ratio=None,
                                        enterprise_value_to_ebitda_ratio=None,
                                        enterprise_value_to_revenue_ratio=None,
                                        free_cash_flow_yield=None,
                                        peg_ratio=None,
                                        gross_margin=None,
                                        operating_margin=None,
                                        net_margin=None,
                                        return_on_equity=None,
                                        return_on_assets=None,
                                        return_on_invested_capital=None,
                                        asset_turnover=None,
                                        inventory_turnover=None,
                                        receivables_turnover=None,
                                        days_sales_outstanding=None,
                                        operating_cycle=None,
                                        working_capital_turnover=None,
                                        current_ratio=None,
                                        quick_ratio=None,
                                        cash_ratio=None,
                                        operating_cash_flow_ratio=None,
                                        debt_to_equity=None,
                                        debt_to_assets=None,
                                        interest_coverage=None,
                                        revenue_growth=None,
                                        earnings_growth=None,
                                        book_value_growth=None,
                                        earnings_per_share_growth=None,
                                        free_cash_flow_growth=None,
                                        operating_income_growth=None,
                                        ebitda_growth=None,
                                        payout_ratio=None,
                                        earnings_per_share=float(period_data["v"]) if key_metric.startswith("eps") else None,
                                        book_value_per_share=None,
                                        free_cash_flow_per_share=None
                                    )
                                    historical_periods.append(historical_metrics)
                            break  

            
            result.extend(historical_periods[:limit-1])  

        
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
    """Fetch insider trades from cache or FinnHub API."""
    
    if cached_data := _cache.get_insider_trades(ticker):
        filtered_data = [InsiderTrade(**trade) for trade in cached_data
                        if (start_date is None or trade["transaction_date"] >= start_date)
                        and trade["transaction_date"] <= end_date]
        filtered_data.sort(key=lambda x: x.transaction_date, reverse=True)
        if filtered_data:
            return filtered_data

    try:
        
        data = finnhub_client.get_insider_transactions(
            ticker,
            from_date=start_date,
            to_date=end_date
        )

        
        trades = []
        for trade in data.get("data", []):
            
            transaction_type = "buy" if trade.get("change") > 0 else "sell"
            shares = abs(trade.get("change", 0))
            price_per_share = trade.get("price", 0)
            total_value = shares * price_per_share

            trades.append(InsiderTrade(
                ticker=ticker,
                issuer=ticker,  
                name=trade.get("name", ""),
                title=trade.get("title", ""),
                is_board_director=None,  
                transaction_date=trade.get("transactionDate", ""),
                transaction_shares=shares,
                transaction_price_per_share=price_per_share,
                transaction_value=total_value,
                shares_owned_before_transaction=None,  
                shares_owned_after_transaction=None,  
                security_title="Common Stock",  
                filing_date=trade.get("filingDate", "")
            ))

        if not trades:
            return []

        
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
    
    if cached_data := _cache.get_company_news(ticker):
        filtered_data = [CompanyNews(**news) for news in cached_data
                        if (start_date is None or news["date"] >= start_date)
                        and news["date"] <= end_date]
        filtered_data.sort(key=lambda x: x.date, reverse=True)
        if filtered_data:
            return filtered_data

    try:
        
        data = finnhub_client.get_company_news(ticker, start_date or "2020-01-01", end_date)

        
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
                sentiment=str(item.get("sentiment", 0))  
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

def search_line_items(
    ticker: str,
    line_items: List[str],
    end_date: str,
    period: str = "ttm",
    limit: int = 10
) -> List[LineItem]:
    """Fetch specific financial line items from FinnHub API."""
    try:
        logger.info(f"Searching line items for {ticker}: {line_items}, period: {period}, limit: {limit}")

        
        metrics_data = finnhub_client.get_basic_financials(ticker, period=period, limit=limit)
        profile = finnhub_client.get_company_profile(ticker);
        metric = metrics_data.get("metric", {})
        series = metrics_data.get("series", {})
        metric["shareOutstanding"] = profile.get("shareOutstanding")

        logger.info(f"Retrieved {len(metric)} metrics and {len(series)} series for {ticker}")

        
        logger.info(f"Available metrics for {ticker} (showing first 20):")
        metric_keys = list(metric.keys())
        for i, key in enumerate(metric_keys[:20]):
            logger.info(f"  {key}: {metric[key]}")
        if len(metric_keys) > 20:
            logger.info(f"  ... and {len(metric_keys) - 20} more metrics")

        
        if series:
            logger.info(f"Available series for {ticker}:")
            for series_type, series_data in series.items():
                if isinstance(series_data, dict):
                    logger.info(f"  {series_type}: {len(series_data)} series - {list(series_data.keys())[:5]}...")
                else:
                    logger.info(f"  {series_type}: {type(series_data)}")

        
        period_suffix = "TTM" if period.lower() == "ttm" else "Annual"
        series_period = "annual" if period.lower() in ["annual", "yearly"] else "quarterly"

        logger.info(f"Using period_suffix: {period_suffix}, series_period: {series_period}")

        
        line_item_map = field_mapping_service.get_mappings_for_source("finnhub", period_suffix)

        
        calculated_mappings = financial_calculator.calculate_missing_metrics(metric, period_suffix)
        line_item_map.update(calculated_mappings)

        
        if period_suffix == "Annual":
            annual_mappings = {
                "total_assets": f"totalAssets{period_suffix}",
                "total_liabilities": f"totalLiabilities{period_suffix}",
                "current_assets": f"currentAssets{period_suffix}",
                "current_liabilities": f"currentLiabilities{period_suffix}",
                "total_debt": f"totalDebt{period_suffix}",
                "inventory": f"inventory{period_suffix}",
                "accounts_receivable": f"accountsReceivable{period_suffix}",
                "short_term_debt": f"shortTermDebt{period_suffix}",
                "working_capital": f"workingCapital{period_suffix}",
                "interest_expense": f"interestExpense{period_suffix}",
            }
            line_item_map.update(annual_mappings)

        logger.info(f"Line item mappings for requested items:")
        for item in line_items:
            mapped_field = line_item_map.get(item)
            logger.info(f"  {item} -> {mapped_field}")
            if mapped_field and mapped_field in metric:
                logger.info(f"    Found in metrics: {metric[mapped_field]}")
            elif mapped_field:
                logger.info(f"    NOT found in metrics")
            else:
                logger.info(f"    No mapping available for period {period_suffix}")

        
        result = []
        for item in line_items:
            logger.info(f"Processing line item: {item}")

            found_value = False

            
            if item in line_item_map and line_item_map[item] is not None:
                finnhub_field = line_item_map[item]
                value = metric.get(finnhub_field)

                logger.info(f"  Mapped to field: {finnhub_field}")
                logger.info(f"  Direct metric value: {value}")

                if value is not None:
                    try:
                        numeric_value = float(value)
                        logger.info(f"  Adding direct metric value: {numeric_value}")
                        result.append(LineItem(
                            name=item,
                            value=numeric_value,
                            report_period=end_date
                        ))
                        found_value = True
                    except (ValueError, TypeError):
                        logger.warning(f"Could not convert value {value} to float for {item}")

            
            if not found_value:
                series_field = field_mapping_service.get_series_mapping("finnhub", item, series_period)
                if series_field:
                    logger.info(f"  Trying series field: {series_field}")

                    if series and series_period in series:
                        period_series = series[series_period]
                        if isinstance(period_series, dict) and series_field in period_series:
                            series_data = period_series[series_field]
                            logger.info(f"  Found {len(series_data) if series_data else 0} series data points for {series_field}")

                            if series_data and isinstance(series_data, list) and len(series_data) > 0:
                                
                                sorted_data = sorted(series_data, key=lambda x: x.get("period", ""), reverse=True)
                                logger.info(f"  Processing {len(sorted_data)} sorted data points")

                                for i, data_point in enumerate(sorted_data[:limit]):
                                    if isinstance(data_point, dict) and data_point.get("v") is not None:
                                        try:
                                            numeric_value = float(data_point["v"])
                                            period_date = data_point.get("period", end_date)
                                            logger.info(f"    Series data point {i}: {numeric_value} for period {period_date}")
                                            result.append(LineItem(
                                                name=item,
                                                value=numeric_value,
                                                report_period=period_date
                                            ))
                                            found_value = True
                                        except (ValueError, TypeError):
                                            logger.warning(f"Could not convert value {data_point['v']} to float for {item}")
                                            continue
                        else:
                            logger.info(f"  Series field {series_field} not found in {series_period} series")
                    else:
                        logger.info(f"  No series data found for period {series_period}")

            if not found_value:
                logger.warning(f"  No data found for {item}")

        
        result.sort(key=lambda x: x.report_period, reverse=True)
        final_result = result[:limit]

        logger.info(f"Final result for {ticker}: {len(final_result)} line items found")
        for item in final_result:
            logger.info(f"  {item.name}: {item.value} (period: {item.report_period})")

        return final_result

    except Exception as e:
        logger.error(f"Error fetching line items for {ticker}: {str(e)}")
        raise

def calculate_growth_rates(
    ticker: str,
    metrics: List[str] = ["revenue", "net_income", "free_cash_flow", "book_value", "ebitda"],
    periods: int = 3,
    period: str = "ttm"
) -> dict:
    """Calculate growth rates for financial metrics using historical data."""
    try:
        
        metrics_data = finnhub_client.get_basic_financials(ticker, period=period)
        series = metrics_data.get("series", {})

        
        if period.lower() == "ttm":
            
            series_data = series.get("annual", {})  
        elif period.lower() in ["annual", "yearly"]:
            series_data = series.get("annual", {})
        else:
            series_data = series.get("annual", {})  

        growth_rates = {}

        suffix = "Annual" if period.lower() in ["annual", "yearly"] else "TTM"

        metric_mappings = {
            "revenue": [f"revenuePerShare{suffix}", f"revenue{suffix}"],
            "net_income": [f"netIncome{suffix}", f"netProfitMargin{suffix}"],
            "free_cash_flow": [f"freeCashFlow{suffix}"],
            "book_value": [f"bookValuePerShare{suffix}", f"tangibleBookValuePerShare{suffix}"],
            "ebitda": [f"ebitda{suffix}"],
            "operating_income": [f"operatingIncome{suffix}", f"operatingMargin{suffix}"],
            "total_assets": [f"totalAssets{suffix}"],
            "total_debt": [f"totalDebt{suffix}"],
            "earnings_per_share": [f"epsBasicExclExtraItems{suffix}"]
        }

        if period.lower() == "ttm":
            for metric_name in metric_mappings:
                ttm_fields = [field.replace("TTM", "Annual") for field in metric_mappings[metric_name]]
                metric_mappings[metric_name].extend(ttm_fields)

        for metric_name in metrics:
            if metric_name not in metric_mappings:
                continue

            historical_data = None
            for field_name in metric_mappings[metric_name]:
                if field_name in series_data:
                    historical_data = series_data[field_name]
                    break

            if not historical_data or len(historical_data) < 2:
                growth_rates[f"{metric_name}_growth"] = None
                continue

            sorted_data = sorted(historical_data, key=lambda x: x.get("period", ""), reverse=True)

            if len(sorted_data) >= 2:
                try:
                    current_value = float(sorted_data[0]["v"])
                    previous_value = float(sorted_data[1]["v"])

                    if previous_value != 0:
                        growth_rate = (current_value - previous_value) / abs(previous_value)
                        growth_rates[f"{metric_name}_growth"] = growth_rate
                    else:
                        growth_rates[f"{metric_name}_growth"] = None

                    if len(sorted_data) >= periods:
                        oldest_value = float(sorted_data[periods-1]["v"])
                        if oldest_value != 0:
                            years = periods - 1
                            cagr = (abs(current_value / oldest_value) ** (1/years)) - 1
                            if current_value < 0 and oldest_value < 0:
                                cagr = -cagr  
                            growth_rates[f"{metric_name}_cagr_{periods}y"] = cagr
                        else:
                            growth_rates[f"{metric_name}_cagr_{periods}y"] = None

                except (ValueError, TypeError, ZeroDivisionError):
                    growth_rates[f"{metric_name}_growth"] = None
            else:
                growth_rates[f"{metric_name}_growth"] = None

        return growth_rates

    except Exception as e:
        logger.error(f"Error calculating growth rates for {ticker}: {str(e)}")
        return {}
