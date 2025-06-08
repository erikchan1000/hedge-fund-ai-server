from typing import Optional, Dict, Any
from data.models import FinancialMetrics

def _get_series_value(series: Dict[str, Any], key: str, period: str = "ttm") -> Optional[float]:
    """Get value from series data, respecting the period parameter.
    
    Args:
        series: The series data from Finnhub
        key: The key to look up
        period: Either "ttm" or "annual"
    """
    if not series:
        return None
        
    # For TTM, prefer quarterly data
    if period == "ttm":
        sources = ['quarterly', 'annual']
    else:
        # For annual, only use annual data
        sources = ['annual']
        
    for source in sources:
        if source in series and key in series[source] and series[source][key]:
            val = series[source][key][0]
            if isinstance(val, dict):
                return val.get('v')
            return val
    return None

def _get_metric_value(metric: Dict[str, Any], ttm_key: str, annual_key: str, period: str = "ttm") -> Optional[float]:
    """Get value from metric data, respecting the period parameter.
    
    Args:
        metric: The metric data from Finnhub
        ttm_key: The key for TTM value
        annual_key: The key for annual value
        period: Either "ttm" or "annual"
    """
    if period == "ttm":
        return metric.get(ttm_key) or metric.get(annual_key)
    return metric.get(annual_key) or metric.get(ttm_key)

def _calculate_growth(series: Dict[str, Any], key: str) -> Optional[float]:
    """Calculate growth rate from series data."""
    data = None
    if series and 'quarterly' in series and key in series['quarterly']:
        data = series['quarterly'][key]
    elif series and 'annual' in series and key in series['annual']:
        data = series['annual'][key]
    if data and len(data) >= 2:
        current = data[0]['v']
        previous = data[1]['v']
        try:
            return (current - previous) / previous if previous else None
        except Exception:
            return None
    return None

def _calculate_dso(metric: Dict[str, Any], series: Dict[str, Any]) -> Optional[float]:
    """Calculate Days Sales Outstanding."""
    receivables_turnover = (
        _get_series_value(series, 'receivablesTurnoverTTM') or
        _get_series_value(series, 'receivablesTurnover') or
        metric.get('receivablesTurnoverTTM') or
        metric.get('receivablesTurnoverAnnual')
    )
    return 365 / receivables_turnover if receivables_turnover else None

def _calculate_operating_cycle(metric: Dict[str, Any], series: Dict[str, Any]) -> Optional[float]:
    """Calculate Operating Cycle."""
    inventory_turnover = (
        _get_series_value(series, 'inventoryTurnoverTTM') or
        _get_series_value(series, 'inventoryTurnover') or
        metric.get('inventoryTurnoverTTM') or
        metric.get('inventoryTurnoverAnnual')
    )
    receivables_turnover = (
        _get_series_value(series, 'receivablesTurnoverTTM') or
        _get_series_value(series, 'receivablesTurnover') or
        metric.get('receivablesTurnoverTTM') or
        metric.get('receivablesTurnoverAnnual')
    )
    if inventory_turnover and receivables_turnover:
        dio = 365 / inventory_turnover
        dso = 365 / receivables_turnover
        return dio + dso
    return None

def _calculate_wc_turnover(metric: Dict[str, Any], series: Dict[str, Any]) -> Optional[float]:
    """Calculate Working Capital Turnover."""
    asset_turnover = _get_series_value(series, 'assetTurnoverTTM') or metric.get('assetTurnoverTTM')
    current_ratio = _get_series_value(series, 'currentRatio') or metric.get('currentRatioQuarterly')
    if asset_turnover and current_ratio:
        return asset_turnover * (current_ratio - 1 if current_ratio > 1 else 0.5)
    return None

def _calculate_ocf_ratio(metric: Dict[str, Any], series: Dict[str, Any]) -> Optional[float]:
    """Calculate Operating Cash Flow Ratio."""
    fcf_margin = _get_series_value(series, 'fcfMargin')
    current_ratio = _get_series_value(series, 'currentRatio') or metric.get('currentRatioQuarterly')
    if fcf_margin and current_ratio:
        return (fcf_margin / 100) * current_ratio
    if metric.get('cashFlowPerShareTTM') and metric.get('revenuePerShareTTM') and metric.get('currentRatioQuarterly'):
        return (metric['cashFlowPerShareTTM'] / metric['revenuePerShareTTM']) * metric['currentRatioQuarterly']
    return None

def _calculate_debt_to_assets(metric: Dict[str, Any]) -> Optional[float]:
    """Calculate Debt to Assets ratio."""
    debt_to_equity = metric.get('totalDebtToTotalEquityQuarterly') or metric.get('totalDebtToTotalEquityAnnual')
    if debt_to_equity:
        return debt_to_equity / (1 + debt_to_equity)
    return None

def _calculate_ev_to_ebitda(metric: Dict[str, Any]) -> Optional[float]:
    """Calculate Enterprise Value to EBITDA ratio."""
    return metric.get('currentEvPerfreeCashFlowTTM') or metric.get('currentEvPerfreeCashFlowAnnual')

def _calculate_ev_to_revenue(metric: Dict[str, Any]) -> Optional[float]:
    """Calculate Enterprise Value to Revenue ratio."""
    return metric.get('psTTM') or metric.get('psAnnual')

def _calculate_fcf_yield(metric: Dict[str, Any]) -> Optional[float]:
    """Calculate Free Cash Flow Yield."""
    if metric.get('currentEvPerfreeCashFlowTTM'):
        return 1 / metric['currentEvPerfreeCashFlowTTM']
    return None

def _calculate_peg_ratio(metric: Dict[str, Any]) -> Optional[float]:
    """Calculate PEG Ratio."""
    pe = metric.get('peTTM') or metric.get('peAnnual')
    growth = metric.get('epsGrowth5Y')
    if pe and growth and growth > 0:
        return pe / growth
    return None

def _calculate_book_value_per_share(series: Dict[str, Any], metric: Dict[str, Any]) -> Optional[float]:
    """Calculate Book Value per Share."""
    val = _get_series_value(series, 'bookValue')
    if val:
        return val
    return metric.get('bookValuePerShareQuarterly') or metric.get('bookValuePerShareAnnual')

def map_finnhub_metric_to_financial_metrics(
    ticker: str,
    metrics_data: Dict[str, Any],
    end_date: str,
    period: str = "ttm",
    currency: str = "USD"
) -> FinancialMetrics:
    """Map Finnhub metric response to FinancialMetrics model.
    
    Args:
        ticker: The stock ticker
        metrics_data: The raw metrics data from Finnhub
        end_date: The end date for the metrics
        period: Either "ttm" or "annual"
        currency: The currency code
    """
    metric = metrics_data.get("metric", {})
    series = metrics_data.get("series", {})
    
    # Helper to get metric value with period preference
    def get_metric(ttm_key: str, annual_key: str) -> Optional[float]:
        return _get_metric_value(metric, ttm_key, annual_key, period)
    
    # Helper to get series value with period preference
    def get_series(key: str) -> Optional[float]:
        return _get_series_value(series, key, period)
    
    return FinancialMetrics(
        ticker=ticker,
        report_period=end_date,
        period=period,
        currency=currency,
        market_cap=(metric.get("marketCapitalization") * 1_000_000) if metric.get("marketCapitalization") else None,
        enterprise_value=(
            (_get_series_value(series, 'ev', period) or metric.get('enterpriseValue')) * 1_000_000
            if (_get_series_value(series, 'ev', period) or metric.get('enterpriseValue')) else None
        ),
        price_to_earnings_ratio=
            get_series('peTTM') or get_series('pe') or get_metric('peTTM', 'peAnnual'),
        price_to_book_ratio=
            get_series('pb') or get_metric('pbTTM', 'pbAnnual'),
        price_to_sales_ratio=
            get_series('psTTM') or get_series('ps') or get_metric('psTTM', 'psAnnual'),
        enterprise_value_to_ebitda_ratio=_calculate_ev_to_ebitda(metric),
        enterprise_value_to_revenue_ratio=_calculate_ev_to_revenue(metric),
        free_cash_flow_yield=_calculate_fcf_yield(metric),
        peg_ratio=_calculate_peg_ratio(metric),
        gross_margin=(
            (get_series('grossMargin') or get_metric('grossMarginTTM', 'grossMarginAnnual'))
            / 100 if (get_series('grossMargin') or get_metric('grossMarginTTM', 'grossMarginAnnual')) else None
        ),
        operating_margin=(
            (get_series('operatingMargin') or get_metric('operatingMarginTTM', 'operatingMarginAnnual'))
            / 100 if (get_series('operatingMargin') or get_metric('operatingMarginTTM', 'operatingMarginAnnual')) else None
        ),
        net_margin=(
            (get_series('netMargin') or get_metric('netProfitMarginTTM', 'netProfitMarginAnnual'))
            / 100 if (get_series('netMargin') or get_metric('netProfitMarginTTM', 'netProfitMarginAnnual')) else None
        ),
        return_on_equity=(
            (get_series('roeTTM') or get_series('roe') or get_metric('roeTTM', 'roeRfy'))
            / 100 if (get_series('roeTTM') or get_series('roe') or get_metric('roeTTM', 'roeRfy')) else None
        ),
        return_on_assets=(
            (get_series('roaTTM') or get_series('roa') or get_metric('roaTTM', 'roaRfy'))
            / 100 if (get_series('roaTTM') or get_series('roa') or get_metric('roaTTM', 'roaRfy')) else None
        ),
        return_on_invested_capital=(
            (get_series('roicTTM') or get_series('roic') or get_metric('roiTTM', 'roiAnnual'))
            / 100 if (get_series('roicTTM') or get_series('roic') or get_metric('roiTTM', 'roiAnnual')) else None
        ),
        asset_turnover=get_series('assetTurnoverTTM') or get_metric('assetTurnoverTTM', 'assetTurnoverAnnual'),
        inventory_turnover=get_series('inventoryTurnoverTTM') or get_series('inventoryTurnover') or get_metric('inventoryTurnoverTTM', 'inventoryTurnoverAnnual'),
        receivables_turnover=get_series('receivablesTurnoverTTM') or get_series('receivablesTurnover') or get_metric('receivablesTurnoverTTM', 'receivablesTurnoverAnnual'),
        days_sales_outstanding=_calculate_dso(metric, series),
        operating_cycle=_calculate_operating_cycle(metric, series),
        working_capital_turnover=_calculate_wc_turnover(metric, series),
        current_ratio=get_series('currentRatio') or get_metric('currentRatioQuarterly', 'currentRatioAnnual'),
        quick_ratio=get_series('quickRatio') or get_metric('quickRatioQuarterly', 'quickRatioAnnual'),
        cash_ratio=series.get('annual', {}).get('cashRatio', [{}])[0].get('v') if series.get('annual', {}).get('cashRatio') else None,
        operating_cash_flow_ratio=_calculate_ocf_ratio(metric, series),
        debt_to_equity=get_series('totalDebtToEquity') or get_metric('totalDebtToTotalEquityQuarterly', 'totalDebtToTotalEquityAnnual'),
        debt_to_assets=get_series('totalDebtToTotalAsset') or _calculate_debt_to_assets(metric),
        interest_coverage=get_metric('netInterestCoverageTTM', 'netInterestCoverageAnnual'),
        revenue_growth=_calculate_growth(series, 'salesPerShare') or (get_metric('revenueGrowthTTMYoy', 'revenueGrowth5Y') / 100 if get_metric('revenueGrowthTTMYoy', 'revenueGrowth5Y') else None),
        earnings_growth=_calculate_growth(series, 'eps') or (get_metric('epsGrowthTTMYoy', 'epsGrowth5Y') / 100 if get_metric('epsGrowthTTMYoy', 'epsGrowth5Y') else None),
        book_value_growth=_calculate_growth(series, 'bookValue') or (get_metric('bookValueShareGrowthTTM', 'bookValueShareGrowth5Y') / 100 if get_metric('bookValueShareGrowthTTM', 'bookValueShareGrowth5Y') else None),
        earnings_per_share_growth=_calculate_growth(series, 'eps') or (get_metric('epsGrowthTTMYoy', 'epsGrowth5Y') / 100 if get_metric('epsGrowthTTMYoy', 'epsGrowth5Y') else None),
        free_cash_flow_growth=_calculate_growth(series, 'fcfMargin') or (get_metric('focfCagrTTM', 'focfCagr5Y') / 100 if get_metric('focfCagrTTM', 'focfCagr5Y') else None),
        operating_income_growth=_calculate_growth(series, 'operatingMargin') or (get_metric('revenueGrowthTTMYoy', 'revenueGrowth5Y') / 100 if get_metric('revenueGrowthTTMYoy', 'revenueGrowth5Y') else None),
        ebitda_growth=_calculate_growth(series, 'ebitPerShare') or (get_metric('ebitdaCagrTTM', 'ebitdaCagr5Y') / 100 if get_metric('ebitdaCagrTTM', 'ebitdaCagr5Y') else None),
        payout_ratio=(
            (get_series('payoutRatioTTM') or get_series('payoutRatio') or get_metric('payoutRatioTTM', 'payoutRatioAnnual'))
            / 100 if (get_series('payoutRatioTTM') or get_series('payoutRatio') or get_metric('payoutRatioTTM', 'payoutRatioAnnual')) else None
        ),
        earnings_per_share=get_series('eps') or get_metric('epsTTM', 'epsAnnual'),
        book_value_per_share=_calculate_book_value_per_share(series, metric),
        free_cash_flow_per_share=get_series('fcfPerShareTTM') or get_metric('cashFlowPerShareTTM', 'cashFlowPerShareAnnual')
    ) 