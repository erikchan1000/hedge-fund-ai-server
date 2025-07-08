from pydantic import BaseModel
from enum import Enum


class SentimentType(str, Enum):
    """Enum for news sentiment analysis"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class Price(BaseModel):
    open: float
    close: float
    high: float
    low: float
    volume: int
    time: str


class PriceResponse(BaseModel):
    ticker: str
    prices: list[Price]


class FinancialMetrics(BaseModel):
    ticker: str
    report_period: str
    period: str | None = None
    currency: str | None = None
    market_cap: float | None = None
    enterprise_value: float | None = None
    price_to_earnings_ratio: float | None = None
    price_to_book_ratio: float | None = None
    price_to_sales_ratio: float | None = None
    enterprise_value_to_ebitda_ratio: float | None = None
    enterprise_value_to_revenue_ratio: float | None = None
    free_cash_flow_yield: float | None = None
    peg_ratio: float | None = None
    gross_margin: float | None = None
    operating_margin: float | None = None
    net_margin: float | None = None
    return_on_equity: float | None = None
    return_on_assets: float | None = None
    return_on_invested_capital: float | None = None
    asset_turnover: float | None = None
    inventory_turnover: float | None = None
    receivables_turnover: float | None = None
    days_sales_outstanding: float | None = None
    operating_cycle: float | None = None
    working_capital_turnover: float | None = None
    current_ratio: float | None = None
    quick_ratio: float | None = None
    cash_ratio: float | None = None
    operating_cash_flow_ratio: float | None = None
    debt_to_equity: float | None = None
    debt_to_assets: float | None = None
    interest_coverage: float | None = None
    revenue_growth: float | None = None
    earnings_growth: float | None = None
    book_value_growth: float | None = None
    earnings_per_share_growth: float | None = None
    free_cash_flow_growth: float | None = None
    operating_income_growth: float | None = None
    ebitda_growth: float | None = None
    payout_ratio: float | None = None
    earnings_per_share: float | None = None
    book_value_per_share: float | None = None
    free_cash_flow_per_share: float | None = None


class FinancialMetricsResponse(BaseModel):
    financial_metrics: list[FinancialMetrics]


class LineItem(BaseModel):
    ticker: str
    report_period: str
    period: str
    currency: str

    # Allow additional fields dynamically
    model_config = {"extra": "allow"}


class LineItemResponse(BaseModel):
    search_results: list[LineItem]


class InsiderTrade(BaseModel):
    ticker: str
    issuer: str | None
    name: str | None
    title: str | None
    is_board_director: bool | None
    transaction_date: str | None
    transaction_shares: float | None
    transaction_price_per_share: float | None
    transaction_value: float | None
    shares_owned_before_transaction: float | None
    shares_owned_after_transaction: float | None
    security_title: str | None
    filing_date: str


class InsiderTradeResponse(BaseModel):
    insider_trades: list[InsiderTrade]


class CompanyNews(BaseModel):
    ticker: str
    title: str
    author: str
    source: str
    date: str
    url: str
    sentiment: SentimentType | None = None


class CompanyNewsResponse(BaseModel):
    news: list[CompanyNews]


class CompanyFacts(BaseModel):
    ticker: str
    name: str
    cik: str | None = None
    industry: str | None = None
    sector: str | None = None
    category: str | None = None
    exchange: str | None = None
    is_active: bool | None = None
    listing_date: str | None = None
    location: str | None = None
    market_cap: float | None = None
    number_of_employees: int | None = None
    sec_filings_url: str | None = None
    sic_code: str | None = None
    sic_industry: str | None = None
    sic_sector: str | None = None
    website_url: str | None = None
    weighted_average_shares: int | None = None


class CompanyFactsResponse(BaseModel):
    company_facts: CompanyFacts


class Position(BaseModel):
    cash: float = 0.0
    shares: int = 0
    ticker: str


class Portfolio(BaseModel):
    positions: dict[str, Position]  # ticker -> Position mapping
    total_cash: float = 0.0


class AnalystSignal(BaseModel):
    signal: str | None = None
    confidence: float | None = None
    reasoning: dict | str | None = None
    max_position_size: float | None = None  # For risk management signals


class TickerAnalysis(BaseModel):
    ticker: str
    analyst_signals: dict[str, AnalystSignal]  # agent_name -> signal mapping


class AgentStateData(BaseModel):
    tickers: list[str]
    portfolio: Portfolio
    start_date: str
    end_date: str
    ticker_analyses: dict[str, TickerAnalysis]  # ticker -> analysis mapping


class AgentStateMetadata(BaseModel):
    show_reasoning: bool = False
    model_config = {"extra": "allow"}


class FinancialPeriod(str, Enum):
    TTM = "ttm"
    ANNUAL = "annual"
    QUARTERLY = "quarterly"


class LineItemName(str, Enum):
    """Comprehensive enum of all financial line items used across the hedge fund analysis system"""
    
    # Core Financial Statement Items
    REVENUE = "revenue"
    TOTAL_REVENUE = "total_revenue"
    NET_INCOME = "net_income"
    OPERATING_INCOME = "operating_income"
    GROSS_PROFIT = "gross_profit"
    EBIT = "ebit"
    EBITDA = "ebitda"
    
    # Balance Sheet - Assets
    TOTAL_ASSETS = "total_assets"
    CURRENT_ASSETS = "current_assets"
    NONCURRENT_ASSETS = "noncurrent_assets"
    CASH_AND_EQUIVALENTS = "cash_and_equivalents"
    CASH = "cash"
    ACCOUNTS_RECEIVABLE = "accounts_receivable"
    INVENTORY = "inventory"
    PREPAID_EXPENSES = "prepaid_expenses"
    OTHER_CURRENT_ASSETS = "other_current_assets"
    FIXED_ASSETS = "fixed_assets"
    INTANGIBLE_ASSETS = "intangible_assets"
    LONG_TERM_INVESTMENTS = "long_term_investments"
    OTHER_NONCURRENT_ASSETS = "other_noncurrent_assets"
    
    # Balance Sheet - Liabilities
    TOTAL_LIABILITIES = "total_liabilities"
    CURRENT_LIABILITIES = "current_liabilities"
    NONCURRENT_LIABILITIES = "noncurrent_liabilities"
    ACCOUNTS_PAYABLE = "accounts_payable"
    INTEREST_PAYABLE = "interest_payable"
    WAGES = "wages"
    OTHER_CURRENT_LIABILITIES = "other_current_liabilities"
    LONG_TERM_DEBT = "long_term_debt"
    SHORT_TERM_DEBT = "short_term_debt"
    TOTAL_DEBT = "total_debt"
    
    # Balance Sheet - Equity
    SHAREHOLDERS_EQUITY = "shareholders_equity"
    TOTAL_EQUITY = "total_equity"
    EQUITY_ATTRIBUTABLE_TO_PARENT = "equity_attributable_to_parent"
    EQUITY_ATTRIBUTABLE_TO_NONCONTROLLING_INTEREST = "equity_attributable_to_noncontrolling_interest"
    RETAINED_EARNINGS = "retained_earnings"
    
    # Cash Flow Statement
    FREE_CASH_FLOW = "free_cash_flow"
    OPERATING_CASH_FLOW = "operating_cash_flow"
    INVESTING_CASH_FLOW = "investing_cash_flow"
    FINANCING_CASH_FLOW = "financing_cash_flow"
    CAPITAL_EXPENDITURE = "capital_expenditure"
    DEPRECIATION_AND_AMORTIZATION = "depreciation_and_amortization"
    WORKING_CAPITAL = "working_capital"
    DIVIDENDS_AND_OTHER_CASH_DISTRIBUTIONS = "dividends_and_other_cash_distributions"
    ISSUANCE_OR_PURCHASE_OF_EQUITY_SHARES = "issuance_or_purchase_of_equity_shares"
    
    # Per Share Metrics
    EARNINGS_PER_SHARE = "earnings_per_share"
    BOOK_VALUE_PER_SHARE = "book_value_per_share"
    REVENUE_PER_SHARE = "revenue_per_share"
    FREE_CASH_FLOW_PER_SHARE = "free_cash_flow_per_share"
    DIVIDENDS_PER_SHARE = "dividends_per_share"
    
    # Share Information
    OUTSTANDING_SHARES = "outstanding_shares"
    SHARES_OUTSTANDING = "shares_outstanding"
    BASIC_SHARES_OUTSTANDING = "basic_shares_outstanding"
    DILUTED_SHARES_OUTSTANDING = "diluted_shares_outstanding"
    
    # Margins & Ratios
    GROSS_MARGIN = "gross_margin"
    OPERATING_MARGIN = "operating_margin"
    NET_MARGIN = "net_margin"
    CURRENT_RATIO = "current_ratio"
    DEBT_TO_EQUITY_RATIO = "debt_to_equity_ratio"
    RETURN_ON_EQUITY = "return_on_equity"
    RETURN_ON_ASSETS = "return_on_assets"
    
    # Additional Calculated Metrics
    ENTERPRISE_VALUE = "enterprise_value"
    MARKET_CAPITALIZATION = "market_capitalization"
    PRICE_TO_EARNINGS_RATIO = "price_to_earnings_ratio"
    PRICE_TO_BOOK_RATIO = "price_to_book_ratio"
    PRICE_TO_SALES_RATIO = "price_to_sales_ratio"
