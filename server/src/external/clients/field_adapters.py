from typing import Dict, Optional, List, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

class FieldAdapter(ABC):
    """Abstract base class for field name adapters."""
    
    @abstractmethod
    def get_direct_mapping(self, line_item: str, period_suffix: str) -> Optional[str]:
        """Get direct field mapping for a line item."""
        pass
    
    @abstractmethod
    def get_series_mapping(self, line_item: str, period_key: str) -> Optional[str]:
        """Get series field mapping for a line item."""
        pass
    
    @abstractmethod
    def get_all_mappings(self, period_suffix: str) -> Dict[str, Optional[str]]:
        """Get all direct field mappings for a given period."""
        pass

class FinnHubFieldAdapter(FieldAdapter):
    """Adapter for FinnHub API field mappings."""
    
    def __init__(self):
        # Base mappings that work across periods
        self.base_mappings = {
            "earnings_per_share": "epsBasicExclExtraItems",
            "revenue": "revenuePerShare", 
            "book_value_per_share": "bookValuePerShare",
            "operating_cash_flow": "cashFlowPerShare",
            "cash_and_equivalents": "cashPerSharePerShare",
            "dividends_and_other_cash": "dividendPerShare",
            "gross_profit": "grossMargin",
            "operating_income": "operatingMargin",
        }
        
        # Period-specific mappings (TTM vs Annual)
        self.period_specific_mappings = {
            "net_income": {
                "TTM": "netProfitMargin",  # This is a margin, not absolute value
                "Annual": "netProfitMargin"
            }
        }
        
        # Annual-only mappings (not available for TTM)
        self.annual_only_mappings = {
            "total_assets": "totalAssets",
            "total_liabilities": "totalLiabilities",
            "current_assets": "currentAssets", 
            "current_liabilities": "currentLiabilities",
            "total_debt": "totalDebt",
            "inventory": "inventory",
            "accounts_receivable": "accountsReceivable",
            "short_term_debt": "shortTermDebt",
            "working_capital": "workingCapital",
            "long_term_debt": "longTermDebt/equity",
            "interest_expense": "interestExpense",
        }
        
        # Series field mappings (for historical data in series section)
        self.series_mappings = {
            "net_income": "netIncome",
            "revenue": "totalRevenue",
            "free_cash_flow": "freeCashFlow", 
            "operating_cash_flow": "operatingCashFlow",
            "total_assets": "totalAssets",
            "total_debt": "totalDebt",
            "current_assets": "currentAssets",
            "current_liabilities": "currentLiabilities",
            "working_capital": "workingCapital",
            "capital_expenditure": "capitalExpenditure",
            "capital_expenditures": "capitalExpenditure",
            "depreciation_and_amortization": "depreciationAmortization",
            "cash_and_equivalents": "cashAndCashEquivalents",
            "inventory": "inventory",
            "accounts_receivable": "accountsReceivable",
            "interest_expense": "interestExpense",
            "gross_profit": "grossProfit",
            "operating_income": "operatingIncome",
            "ebitda": "ebitda",
            "research_and_development": "researchAndDevelopment",
        }
    
    def get_direct_mapping(self, line_item: str, period_suffix: str) -> Optional[str]:
        """Get direct field mapping for a line item with period suffix."""
        
        # Check period-specific mappings first
        if line_item in self.period_specific_mappings:
            period_mappings = self.period_specific_mappings[line_item]
            if period_suffix in period_mappings:
                return f"{period_mappings[period_suffix]}{period_suffix}"
        
        # Check base mappings with period suffix
        if line_item in self.base_mappings:
            return f"{self.base_mappings[line_item]}{period_suffix}"
        
        # Check annual-only mappings (only for Annual period)
        if period_suffix == "Annual" and line_item in self.annual_only_mappings:
            return f"{self.annual_only_mappings[line_item]}{period_suffix}"
        
        # Items that don't have TTM equivalents
        if period_suffix == "TTM" and line_item in [
            "total_assets", "total_liabilities", "current_assets", "current_liabilities",
            "total_debt", "inventory", "accounts_receivable", "short_term_debt", 
            "working_capital", "capital_expenditure", "capital_expenditures",
            "depreciation_and_amortization", "interest_expense"
        ]:
            return None
        
        return None
    
    def get_series_mapping(self, line_item: str, period_key: str) -> Optional[str]:
        """Get series field mapping for a line item."""
        return self.series_mappings.get(line_item)
    
    def get_all_mappings(self, period_suffix: str) -> Dict[str, Optional[str]]:
        """Get all direct field mappings for a given period."""
        mappings = {}
        
        # Add base mappings with period suffix
        for line_item, base_field in self.base_mappings.items():
            mappings[line_item] = f"{base_field}{period_suffix}"
        
        # Add period-specific mappings
        for line_item, period_mappings in self.period_specific_mappings.items():
            if period_suffix in period_mappings:
                mappings[line_item] = f"{period_mappings[period_suffix]}{period_suffix}"
        
        # Add annual-only mappings if period is Annual
        if period_suffix == "Annual":
            for line_item, field in self.annual_only_mappings.items():
                mappings[line_item] = f"{field}{period_suffix}"
        else:
            # Set TTM-unavailable fields to None
            for line_item in self.annual_only_mappings.keys():
                mappings[line_item] = None
        
        return mappings
    
    def get_period_key(self, period: str) -> str:
        """Convert period parameter to series period key."""
        if period.lower() == "ttm":
            return "quarterly"  # TTM data often comes from quarterly aggregation
        elif period.lower() in ["annual", "yearly"]:
            return "annual"
        else:
            return "annual"  # default

class PolygonFieldAdapter(FieldAdapter):
    """Adapter for Polygon.io API field mappings."""
    
    def __init__(self):
        # Base mappings for Polygon.io financial data
        self.base_mappings = {
            "earnings_per_share": "basic_earnings_per_share",
            "revenue": "revenues",
            "net_income": "net_income_loss",
            "book_value_per_share": "book_value_per_share",
            "operating_cash_flow": "net_cash_flow_from_operating_activities",
            "free_cash_flow": "free_cash_flow",
            "cash_and_equivalents": "cash_and_cash_equivalents_at_carrying_value",
            "total_assets": "assets",
            "total_liabilities": "liabilities",
            "current_assets": "assets_current",
            "current_liabilities": "liabilities_current",
            "total_debt": "debt",
            "inventory": "inventory",
            "accounts_receivable": "accounts_receivable_net_current",
            "gross_profit": "gross_profit",
            "operating_income": "operating_income_loss",
            "ebitda": "ebitda",
            "interest_expense": "interest_expense",
            "capital_expenditures": "payments_to_acquire_property_plant_and_equipment",
            "depreciation_and_amortization": "depreciation_depletion_and_amortization",
            "research_and_development": "research_and_development_expense",
            "working_capital": "working_capital",
            "dividends_paid": "payments_of_dividends",
        }
        
        # Series field mappings (for historical data)
        self.series_mappings = {
            "net_income": "net_income_loss",
            "revenue": "revenues",
            "free_cash_flow": "free_cash_flow",
            "operating_cash_flow": "net_cash_flow_from_operating_activities",
            "total_assets": "assets",
            "total_debt": "debt",
            "current_assets": "assets_current",
            "current_liabilities": "liabilities_current",
            "working_capital": "working_capital",
            "capital_expenditure": "payments_to_acquire_property_plant_and_equipment",
            "capital_expenditures": "payments_to_acquire_property_plant_and_equipment",
            "depreciation_and_amortization": "depreciation_depletion_and_amortization",
            "cash_and_equivalents": "cash_and_cash_equivalents_at_carrying_value",
            "inventory": "inventory",
            "accounts_receivable": "accounts_receivable_net_current",
            "interest_expense": "interest_expense",
            "gross_profit": "gross_profit",
            "operating_income": "operating_income_loss",
            "ebitda": "ebitda",
            "research_and_development": "research_and_development_expense",
            "earnings_per_share": "basic_earnings_per_share",
        }
    
    def get_direct_mapping(self, line_item: str, period_suffix: str) -> Optional[str]:
        """Get direct field mapping for a line item."""
        # Polygon doesn't use period suffixes in the same way as FinnHub
        # Return the base field name
        return self.base_mappings.get(line_item)
    
    def get_series_mapping(self, line_item: str, period_key: str) -> Optional[str]:
        """Get series field mapping for a line item."""
        return self.series_mappings.get(line_item)
    
    def get_all_mappings(self, period_suffix: str) -> Dict[str, Optional[str]]:
        """Get all direct field mappings for a given period."""
        # For Polygon, we return all base mappings regardless of period
        return self.base_mappings.copy()
    
    def get_period_key(self, period: str) -> str:
        """Convert period parameter to series period key."""
        if period.lower() == "ttm":
            return "quarterly"
        elif period.lower() in ["annual", "yearly"]:
            return "annual"
        else:
            return "annual"

class FieldMappingService:
    """Service to manage field mappings across different data sources."""
    
    def __init__(self):
        self.adapters = {
            "finnhub": FinnHubFieldAdapter(),
            "polygon": PolygonFieldAdapter()
        }
    
    def get_mappings_for_source(self, source: str, period_suffix: str) -> Dict[str, Optional[str]]:
        """Get all field mappings for a specific data source and period."""
        if source not in self.adapters:
            raise ValueError(f"Unknown data source: {source}")
        
        return self.adapters[source].get_all_mappings(period_suffix)
    
    def get_direct_mapping(self, source: str, line_item: str, period_suffix: str) -> Optional[str]:
        """Get direct field mapping for a specific line item."""
        if source not in self.adapters:
            raise ValueError(f"Unknown data source: {source}")
        
        return self.adapters[source].get_direct_mapping(line_item, period_suffix)
    
    def get_series_mapping(self, source: str, line_item: str, period_key: str) -> Optional[str]:
        """Get series field mapping for a specific line item."""
        if source not in self.adapters:
            raise ValueError(f"Unknown data source: {source}")
        
        return self.adapters[source].get_series_mapping(line_item, period_key)
    
    def get_period_key(self, source: str, period: str) -> str:
        """Get the appropriate period key for series data."""
        if source not in self.adapters:
            raise ValueError(f"Unknown data source: {source}")
        
        return self.adapters[source].get_period_key(period)
    
    def add_adapter(self, source: str, adapter: FieldAdapter):
        """Add a new field adapter for a data source."""
        self.adapters[source] = adapter 

@dataclass
class FinancialMetricsMapping:
    """Definitive mapping for financial metrics fields"""
    # Market & Valuation
    market_cap: str
    enterprise_value: str
    price_to_earnings_ratio: str
    price_to_book_ratio: str
    price_to_sales_ratio: str
    enterprise_value_to_ebitda_ratio: str
    enterprise_value_to_revenue_ratio: str
    free_cash_flow_yield: str
    peg_ratio: str
    
    # Profitability & Margins
    gross_margin: str
    operating_margin: str
    net_margin: str
    return_on_equity: str
    return_on_assets: str
    return_on_invested_capital: str
    
    # Activity & Efficiency
    asset_turnover: str
    inventory_turnover: str
    receivables_turnover: str
    
    # Liquidity
    current_ratio: str
    quick_ratio: str
    cash_ratio: str
    operating_cash_flow_ratio: str
    
    # Leverage
    debt_to_equity: str
    debt_to_assets: str
    interest_coverage: str
    
    # Growth
    revenue_growth: str
    earnings_growth: str
    book_value_growth: str
    earnings_per_share_growth: str
    free_cash_flow_growth: str
    operating_income_growth: str
    ebitda_growth: str
    
    # Per Share
    earnings_per_share: str
    book_value_per_share: str
    free_cash_flow_per_share: str
    payout_ratio: str

class PolygonFinancialMetricsAdapter:
    """Adapter to transform Polygon API response to standard FinancialMetrics fields"""
    
    def __init__(self):
        # Define mappings for TTM and Annual periods
        self.ttm_mapping = FinancialMetricsMapping(
            # Market & Valuation
            market_cap="marketCapitalization",
            enterprise_value="enterpriseValue",
            price_to_earnings_ratio="peTTM",
            price_to_book_ratio="pbTTM",
            price_to_sales_ratio="psTTM",
            enterprise_value_to_ebitda_ratio="evEbitdaTTM",
            enterprise_value_to_revenue_ratio="evRevenueTTM",
            free_cash_flow_yield="freeCashFlowYieldTTM",
            peg_ratio="pegRatioTTM",
            
            # Profitability & Margins (calculated by polygon client)
            gross_margin="gross_margin",
            operating_margin="operating_margin",
            net_margin="net_margin",
            return_on_equity="return_on_equity",
            return_on_assets="return_on_assets",
            return_on_invested_capital="roicTTM",
            
            # Activity & Efficiency
            asset_turnover="asset_turnover",
            inventory_turnover="inventoryTurnoverTTM",
            receivables_turnover="receivablesTurnoverTTM",
            
            # Liquidity (calculated by polygon client)
            current_ratio="current_ratio",
            quick_ratio="quickRatioTTM",
            cash_ratio="cashRatioTTM",
            operating_cash_flow_ratio="operatingCashFlowRatioTTM",
            
            # Leverage (calculated by polygon client)
            debt_to_equity="debt_to_equity",
            debt_to_assets="debtToAssetsTTM",
            interest_coverage="interestCoverageTTM",
            
            # Growth
            revenue_growth="revenueGrowthTTMYoy",
            earnings_growth="epsGrowthTTMYoy",
            book_value_growth="bookValueGrowthTTMYoy",
            earnings_per_share_growth="epsGrowthTTMYoy",
            free_cash_flow_growth="freeCashFlowGrowthTTMYoy",
            operating_income_growth="operatingIncomeGrowthTTMYoy",
            ebitda_growth="ebitdaGrowthTTMYoy",
            
            # Per Share (calculated by polygon client)
            earnings_per_share="earnings_per_share_basic",
            book_value_per_share="book_value_per_share",
            free_cash_flow_per_share="freeCashFlowPerShareTTM",
            payout_ratio="payoutRatioTTM"
        )
        
        self.annual_mapping = FinancialMetricsMapping(
            # Market & Valuation
            market_cap="marketCapitalization",
            enterprise_value="enterpriseValue",
            price_to_earnings_ratio="peAnnual",
            price_to_book_ratio="pbAnnual",
            price_to_sales_ratio="psAnnual",
            enterprise_value_to_ebitda_ratio="evEbitdaAnnual",
            enterprise_value_to_revenue_ratio="evRevenueAnnual",
            free_cash_flow_yield="freeCashFlowYieldAnnual",
            peg_ratio="pegRatioAnnual",
            
            # Profitability & Margins (calculated by polygon client)
            gross_margin="gross_margin",
            operating_margin="operating_margin",
            net_margin="net_margin",
            return_on_equity="return_on_equity",
            return_on_assets="return_on_assets",
            return_on_invested_capital="roicAnnual",
            
            # Activity & Efficiency
            asset_turnover="asset_turnover",
            inventory_turnover="inventoryTurnoverAnnual",
            receivables_turnover="receivablesTurnoverAnnual",
            
            # Liquidity (calculated by polygon client)
            current_ratio="current_ratio",
            quick_ratio="quickRatioAnnual",
            cash_ratio="cashRatioAnnual",
            operating_cash_flow_ratio="operatingCashFlowRatioAnnual",
            
            # Leverage (calculated by polygon client)
            debt_to_equity="debt_to_equity",
            debt_to_assets="debtToAssetsAnnual",
            interest_coverage="interestCoverageAnnual",
            
            # Growth
            revenue_growth="revenueGrowthAnnualYoy",
            earnings_growth="epsGrowthAnnualYoy",
            book_value_growth="bookValueGrowthAnnualYoy",
            earnings_per_share_growth="epsGrowthAnnualYoy",
            free_cash_flow_growth="freeCashFlowGrowthAnnualYoy",
            operating_income_growth="operatingIncomeGrowthAnnualYoy",
            ebitda_growth="ebitdaGrowthAnnualYoy",
            
            # Per Share (calculated by polygon client)
            earnings_per_share="earnings_per_share_basic",
            book_value_per_share="book_value_per_share",
            free_cash_flow_per_share="freeCashFlowPerShareAnnual",
            payout_ratio="payoutRatioAnnual"
        )
    
    def transform_to_financial_metrics(
        self, 
        polygon_metrics: Dict[str, Any], 
        period: str,
        shares_outstanding: Optional[float] = None
    ) -> Dict[str, Optional[float]]:
        """
        Transform Polygon API metrics to standard FinancialMetrics fields.
        
        Args:
            polygon_metrics: Raw metrics from Polygon API
            period: "ttm" or "annual"
            shares_outstanding: Share count for per-share calculations
            
        Returns:
            Dictionary with standard field names and values
        """
        mapping = self.ttm_mapping if period.lower() == "ttm" else self.annual_mapping
        result = {}
        
        # Direct field mappings
        for field_name in mapping.__dataclass_fields__.keys():
            polygon_field = getattr(mapping, field_name)
            result[field_name] = polygon_metrics.get(polygon_field)
        
        # Calculate missing metrics using available data
        result.update(self._calculate_missing_metrics(polygon_metrics, period, shares_outstanding))
        
        # Calculate derived ratios if base values are missing
        result.update(self._calculate_derived_ratios(polygon_metrics, result, period))
        
        return result
    
    def _calculate_missing_metrics(
        self, 
        polygon_metrics: Dict[str, Any], 
        period: str,
        shares_outstanding: Optional[float]
    ) -> Dict[str, Optional[float]]:
        """Calculate metrics not directly available from Polygon"""
        calculated = {}
        suffix = "TTM" if period.lower() == "ttm" else "Annual"
        
        # Days sales outstanding from receivables turnover
        receivables_turnover = polygon_metrics.get(f"receivablesTurnover{suffix}")
        if receivables_turnover and receivables_turnover > 0:
            calculated["days_sales_outstanding"] = 365 / receivables_turnover
        
        # Operating cycle
        days_sales_outstanding = calculated.get("days_sales_outstanding")
        inventory_turnover = polygon_metrics.get(f"inventoryTurnover{suffix}")
        if days_sales_outstanding and inventory_turnover and inventory_turnover > 0:
            days_inventory_outstanding = 365 / inventory_turnover
            calculated["operating_cycle"] = days_sales_outstanding + days_inventory_outstanding
        
        # Working capital turnover
        if shares_outstanding:
            revenue_per_share = polygon_metrics.get(f"revenuePerShare{suffix}")
            current_assets = polygon_metrics.get(f"balance_sheet_current_assets{suffix}")
            current_liabilities = polygon_metrics.get(f"balance_sheet_current_liabilities{suffix}")
            
            if revenue_per_share and current_assets and current_liabilities:
                revenue = revenue_per_share * shares_outstanding
                working_capital = current_assets - current_liabilities
                if working_capital > 0:
                    calculated["working_capital_turnover"] = revenue / working_capital
        
        # Free cash flow per share if not available directly
        if not calculated.get("free_cash_flow_per_share") and shares_outstanding:
            operating_cash_flow = polygon_metrics.get(f"cash_flow_statement_net_cash_flow_from_operating_activities{suffix}")
            if operating_cash_flow:
                calculated["free_cash_flow_per_share"] = operating_cash_flow / shares_outstanding
        
        return calculated
    
    def _calculate_derived_ratios(
        self, 
        polygon_metrics: Dict[str, Any], 
        current_result: Dict[str, Optional[float]],
        period: str
    ) -> Dict[str, Optional[float]]:
        """Calculate ratios from base financial statement data if not available directly"""
        calculated = {}
        suffix = "TTM" if period.lower() == "ttm" else "Annual"
        
        # Current ratio
        if not current_result.get("current_ratio"):
            current_assets = polygon_metrics.get(f"balance_sheet_current_assets{suffix}")
            current_liabilities = polygon_metrics.get(f"balance_sheet_current_liabilities{suffix}")
            if current_assets and current_liabilities and current_liabilities != 0:
                calculated["current_ratio"] = current_assets / current_liabilities
        
        # Debt to equity
        if not current_result.get("debt_to_equity"):
            # Try long term debt first, then total liabilities
            debt = (polygon_metrics.get(f"balance_sheet_long_term_debt{suffix}") or 
                   polygon_metrics.get(f"balance_sheet_liabilities{suffix}"))
            equity = polygon_metrics.get(f"balance_sheet_equity{suffix}")
            if debt and equity and equity != 0:
                calculated["debt_to_equity"] = debt / equity
        
        # Debt to assets
        if not current_result.get("debt_to_assets"):
            debt = (polygon_metrics.get(f"balance_sheet_long_term_debt{suffix}") or 
                   polygon_metrics.get(f"balance_sheet_liabilities{suffix}"))
            assets = polygon_metrics.get(f"balance_sheet_assets{suffix}")
            if debt and assets and assets != 0:
                calculated["debt_to_assets"] = debt / assets
        
        # Cash ratio
        if not current_result.get("cash_ratio"):
            cash = polygon_metrics.get(f"balance_sheet_cash{suffix}")
            current_liabilities = polygon_metrics.get(f"balance_sheet_current_liabilities{suffix}")
            if cash and current_liabilities and current_liabilities != 0:
                calculated["cash_ratio"] = cash / current_liabilities
        
        # Operating cash flow ratio
        if not current_result.get("operating_cash_flow_ratio"):
            operating_cash_flow = polygon_metrics.get(f"cash_flow_statement_net_cash_flow_from_operating_activities{suffix}")
            current_liabilities = polygon_metrics.get(f"balance_sheet_current_liabilities{suffix}")
            if operating_cash_flow and current_liabilities and current_liabilities != 0:
                calculated["operating_cash_flow_ratio"] = operating_cash_flow / current_liabilities
        
        return calculated 

@dataclass
class PolygonFinancialData:
    """Raw financial data extracted from Polygon response"""
    # Balance Sheet - Assets
    total_assets: Optional[float] = None
    current_assets: Optional[float] = None
    noncurrent_assets: Optional[float] = None
    inventory: Optional[float] = None
    accounts_receivable: Optional[float] = None
    fixed_assets: Optional[float] = None
    intangible_assets: Optional[float] = None
    other_current_assets: Optional[float] = None
    other_noncurrent_assets: Optional[float] = None
    
    # Balance Sheet - Liabilities
    total_liabilities: Optional[float] = None
    current_liabilities: Optional[float] = None
    noncurrent_liabilities: Optional[float] = None
    accounts_payable: Optional[float] = None
    other_current_liabilities: Optional[float] = None
    wages: Optional[float] = None
    
    # Balance Sheet - Equity
    total_equity: Optional[float] = None
    equity_attributable_to_parent: Optional[float] = None
    equity_attributable_to_noncontrolling_interest: Optional[float] = None
    
    # Income Statement  
    revenues: Optional[float] = None
    cost_of_revenue: Optional[float] = None
    gross_profit: Optional[float] = None
    operating_income: Optional[float] = None
    net_income: Optional[float] = None
    
    basic_eps: Optional[float] = None
    diluted_eps: Optional[float] = None
    basic_shares: Optional[float] = None
    diluted_shares: Optional[float] = None
    common_stock_dividends: Optional[float] = None
    
    # Cash Flow Statement
    operating_cash_flow: Optional[float] = None
    investing_cash_flow: Optional[float] = None
    financing_cash_flow: Optional[float] = None
    net_cash_flow: Optional[float] = None
    
    # Period information
    period: Optional[str] = None
    fiscal_period: Optional[str] = None
    timeframe: Optional[str] = None

class PolygonFinancialAdapter:
    """Definitive adapter for Polygon financial data to FinancialMetrics structure"""
    
    # Exact field mappings - no alternatives, no guessing
    FIELD_MAPPINGS = {
        # Balance Sheet
        'total_assets': 'assets',
        'current_assets': 'current_assets', 
        'noncurrent_assets': 'noncurrent_assets',
        'inventory': 'inventory',
        'accounts_receivable': 'accounts_receivable',
        'fixed_assets': 'fixed_assets',
        'intangible_assets': 'intangible_assets',
        
        'total_liabilities': 'liabilities',
        'current_liabilities': 'current_liabilities',
        'noncurrent_liabilities': 'noncurrent_liabilities',
        'accounts_payable': 'accounts_payable',
        
        'total_equity': 'equity',
        
        # Income Statement
        'revenues': 'revenues',
        'cost_of_revenue': 'cost_of_revenue',
        'gross_profit': 'gross_profit', 
        'operating_income': 'operating_income_loss',
        'net_income': 'net_income_loss',
        
        'basic_eps': 'basic_earnings_per_share',
        'diluted_eps': 'diluted_earnings_per_share',
        'basic_shares': 'basic_average_shares',
        'diluted_shares': 'diluted_average_shares',
        
        # Cash Flow
        'operating_cash_flow': 'net_cash_flow_from_operating_activities',
        'investing_cash_flow': 'net_cash_flow_from_investing_activities',
        'financing_cash_flow': 'net_cash_flow_from_financing_activities',
    }
    
    def extract_financial_data(self, polygon_response: Dict[str, Any]) -> List[PolygonFinancialData]:
        """Extract raw financial data from Polygon response"""
        results = []
        
        for result in polygon_response.get('results', []):
            data = PolygonFinancialData()
            financials = result.get('financials', {})
            
            # Extract from balance sheet
            balance_sheet = financials.get('balance_sheet', {})
            # Assets
            data.total_assets = self._get_value(balance_sheet, 'assets')
            data.current_assets = self._get_value(balance_sheet, 'current_assets')
            data.noncurrent_assets = self._get_value(balance_sheet, 'noncurrent_assets')
            data.inventory = self._get_value(balance_sheet, 'inventory')
            data.accounts_receivable = self._get_value(balance_sheet, 'accounts_receivable')
            data.fixed_assets = self._get_value(balance_sheet, 'fixed_assets')
            data.intangible_assets = self._get_value(balance_sheet, 'intangible_assets')
            data.other_current_assets = self._get_value(balance_sheet, 'other_current_assets')
            data.other_noncurrent_assets = self._get_value(balance_sheet, 'other_noncurrent_assets')
            
            # Liabilities
            data.total_liabilities = self._get_value(balance_sheet, 'liabilities')
            data.current_liabilities = self._get_value(balance_sheet, 'current_liabilities')
            data.noncurrent_liabilities = self._get_value(balance_sheet, 'noncurrent_liabilities')
            data.accounts_payable = self._get_value(balance_sheet, 'accounts_payable')
            data.other_current_liabilities = self._get_value(balance_sheet, 'other_current_liabilities')
            data.wages = self._get_value(balance_sheet, 'wages')
            
            # Equity
            data.total_equity = self._get_value(balance_sheet, 'equity')
            data.equity_attributable_to_parent = self._get_value(balance_sheet, 'equity_attributable_to_parent')
            data.equity_attributable_to_noncontrolling_interest = self._get_value(balance_sheet, 'equity_attributable_to_noncontrolling_interest')
            
            # Extract from income statement
            income_statement = financials.get('income_statement', {})
            data.revenues = self._get_value(income_statement, 'revenues')
            data.cost_of_revenue = self._get_value(income_statement, 'cost_of_revenue')
            data.gross_profit = self._get_value(income_statement, 'gross_profit')
            data.operating_income = self._get_value(income_statement, 'operating_income_loss')
            data.net_income = self._get_value(income_statement, 'net_income_loss')
            data.basic_eps = self._get_value(income_statement, 'basic_earnings_per_share')
            data.diluted_eps = self._get_value(income_statement, 'diluted_earnings_per_share')
            data.basic_shares = self._get_value(income_statement, 'basic_average_shares')
            data.diluted_shares = self._get_value(income_statement, 'diluted_average_shares')
            data.common_stock_dividends = self._get_value(income_statement, 'common_stock_dividends')
            
            # Extract from cash flow statement
            cash_flow = financials.get('cash_flow_statement', {})
            data.operating_cash_flow = self._get_value(cash_flow, 'net_cash_flow_from_operating_activities')
            data.investing_cash_flow = self._get_value(cash_flow, 'net_cash_flow_from_investing_activities')
            data.financing_cash_flow = self._get_value(cash_flow, 'net_cash_flow_from_financing_activities')
            data.net_cash_flow = self._get_value(cash_flow, 'net_cash_flow')
            
            # Add period information
            data.period = result.get('end_date', '')
            data.fiscal_period = result.get('fiscal_period', '')
            data.timeframe = result.get('timeframe', '')
            
            results.append(data)
            
        return results
    
    def calculate_financial_metrics(self, data: PolygonFinancialData, market_cap: Optional[float] = None) -> Dict[str, Optional[float]]:
        """Calculate all financial metrics from raw data"""
        metrics = {}
        
        # Basic values
        metrics['market_cap'] = market_cap
        metrics['earnings_per_share'] = data.basic_eps
        
        # Margin calculations
        if data.revenues and data.revenues > 0:
            if data.gross_profit:
                metrics['gross_margin'] = data.gross_profit / data.revenues
            if data.operating_income:
                metrics['operating_margin'] = data.operating_income / data.revenues  
            if data.net_income:
                metrics['net_margin'] = data.net_income / data.revenues
        
        # Liquidity ratios
        if data.current_assets and data.current_liabilities and data.current_liabilities > 0:
            metrics['current_ratio'] = data.current_assets / data.current_liabilities
        
        # Leverage ratios
        if data.total_equity and data.total_equity > 0:
            if data.noncurrent_liabilities:
                metrics['debt_to_equity'] = data.noncurrent_liabilities / data.total_equity
            if data.net_income:
                metrics['return_on_equity'] = data.net_income / data.total_equity
        
        if data.total_assets and data.total_assets > 0:
            if data.total_liabilities:
                metrics['debt_to_assets'] = data.total_liabilities / data.total_assets
            if data.net_income:
                metrics['return_on_assets'] = data.net_income / data.total_assets
            if data.revenues:
                metrics['asset_turnover'] = data.revenues / data.total_assets
        
        # Turnover ratios
        if data.revenues and data.revenues > 0:
            if data.accounts_receivable and data.accounts_receivable > 0:
                metrics['receivables_turnover'] = data.revenues / data.accounts_receivable
                metrics['days_sales_outstanding'] = 365 / metrics['receivables_turnover']
            if data.inventory and data.inventory > 0:
                inventory_turnover = data.cost_of_revenue / data.inventory if data.cost_of_revenue else None
                if inventory_turnover:
                    metrics['inventory_turnover'] = inventory_turnover
        
        # Per-share calculations
        if data.basic_shares and data.basic_shares > 0:
            if data.total_equity:
                metrics['book_value_per_share'] = data.total_equity / data.basic_shares
            if data.operating_cash_flow:
                metrics['free_cash_flow_per_share'] = data.operating_cash_flow / data.basic_shares
        
        # Cash flow ratios
        if data.operating_cash_flow and data.current_liabilities and data.current_liabilities > 0:
            metrics['operating_cash_flow_ratio'] = data.operating_cash_flow / data.current_liabilities
            
        return metrics
    
    def _get_value(self, section: Dict[str, Any], field_name: str) -> Optional[float]:
        """Extract value from Polygon field structure"""
        field_data = section.get(field_name)
        if field_data and isinstance(field_data, dict):
            value = field_data.get('value')
            if value is not None:
                return float(value)
        return None
    
    def get_line_item_mappings(self, financial_data: PolygonFinancialData) -> Dict[str, Optional[float]]:
        """Get definitive mapping of LineItemName enum values to actual financial data values."""
        
        # Calculate the enhanced fields first
        estimated_capex = self._estimate_capital_expenditure(financial_data)
        estimated_depreciation = self._estimate_depreciation_and_amortization(financial_data)
        enhanced_fcf = self._calculate_enhanced_free_cash_flow(financial_data)
        calculated_working_capital = self._calculate_working_capital(financial_data)
        
        return {
            # Core Financial Statement Items
            "revenue": financial_data.revenues,
            "total_revenue": financial_data.revenues,
            "net_income": financial_data.net_income,  # Direct mapping
            "operating_income": financial_data.operating_income,
            "gross_profit": financial_data.gross_profit,
            "ebit": financial_data.operating_income,  # EBIT ≈ Operating Income
            "ebitda": self._calculate_ebitda(financial_data, estimated_depreciation),  # Enhanced calculation
            
            # Balance Sheet - Assets
            "total_assets": financial_data.total_assets,
            "current_assets": financial_data.current_assets,
            "noncurrent_assets": financial_data.noncurrent_assets,
            "inventory": financial_data.inventory,
            "accounts_receivable": financial_data.accounts_receivable,
            "fixed_assets": financial_data.fixed_assets,
            "intangible_assets": financial_data.intangible_assets,
            "other_current_assets": financial_data.other_current_assets,
            "other_noncurrent_assets": financial_data.other_noncurrent_assets,
            "cash_and_equivalents": None,  # Not available in response
            "cash": None,  # Not available in response
            "prepaid_expenses": None,  # Not available in response
            "long_term_investments": None,  # Not available in response
            
            # Balance Sheet - Liabilities
            "total_liabilities": financial_data.total_liabilities,
            "current_liabilities": financial_data.current_liabilities,
            "noncurrent_liabilities": financial_data.noncurrent_liabilities,
            "accounts_payable": financial_data.accounts_payable,
            "other_current_liabilities": financial_data.other_current_liabilities,
            "wages": financial_data.wages,
            "interest_payable": None,  # Not available in response
            "long_term_debt": None,  # Not explicitly available
            "short_term_debt": None,  # Not explicitly available
            "total_debt": None,  # Cannot calculate without debt components
            
            # Balance Sheet - Equity
            "total_equity": financial_data.total_equity,
            "shareholders_equity": financial_data.total_equity,
            "equity_attributable_to_parent": financial_data.equity_attributable_to_parent,
            "equity_attributable_to_noncontrolling_interest": financial_data.equity_attributable_to_noncontrolling_interest,
            "retained_earnings": None,  # Not available in response
            
            # Cash Flow Statement - Enhanced calculations
            "operating_cash_flow": financial_data.operating_cash_flow,
            "investing_cash_flow": financial_data.investing_cash_flow,
            "financing_cash_flow": financial_data.financing_cash_flow,
            "free_cash_flow": enhanced_fcf,  # Enhanced calculation
            "capital_expenditure": estimated_capex,  # Estimated
            "depreciation_and_amortization": estimated_depreciation,  # Estimated
            "working_capital": calculated_working_capital,  # Calculated
            "dividends_and_other_cash_distributions": None,  # Not available as cash flow item
            "issuance_or_purchase_of_equity_shares": None,  # Not available in response
            
            # Per Share Metrics
            "earnings_per_share": financial_data.basic_eps,
            "book_value_per_share": self._calculate_book_value_per_share(financial_data),
            "revenue_per_share": self._calculate_revenue_per_share(financial_data),
            "free_cash_flow_per_share": self._calculate_enhanced_free_cash_flow_per_share(financial_data, enhanced_fcf),
            "dividends_per_share": financial_data.common_stock_dividends,
            
            # Share Information
            "outstanding_shares": financial_data.basic_shares,
            "shares_outstanding": financial_data.basic_shares,
            "basic_shares_outstanding": financial_data.basic_shares,
            "diluted_shares_outstanding": financial_data.diluted_shares,
            
            # Margins & Ratios (calculated)
            "gross_margin": self._calculate_gross_margin(financial_data),
            "operating_margin": self._calculate_operating_margin(financial_data),
            "net_margin": self._calculate_net_margin(financial_data),
            "current_ratio": self._calculate_current_ratio(financial_data),
            "debt_to_equity_ratio": None,  # Cannot calculate without debt data
            "return_on_equity": self._calculate_return_on_equity(financial_data),
            "return_on_assets": self._calculate_return_on_assets(financial_data),
            
            # Additional Calculated Metrics (require market data)
            "enterprise_value": None,  # Requires market cap + debt - cash
            "market_capitalization": None,  # Requires stock price
            "price_to_earnings_ratio": None,  # Requires stock price
            "price_to_book_ratio": None,  # Requires stock price
            "price_to_sales_ratio": None,  # Requires stock price
        }
    
    def _estimate_capital_expenditure(self, data: PolygonFinancialData) -> Optional[float]:
        """Estimate capital expenditure from investing cash flow.
        
        CapEx is typically the largest component of investing cash flow.
        We estimate it as the negative investing cash flow (rough proxy).
        """
        if data.investing_cash_flow and data.investing_cash_flow < 0:
            # Investing cash flow is typically negative when companies spend on CapEx
            # Return positive value for CapEx
            return abs(data.investing_cash_flow)
        return None
    
    def _estimate_depreciation_and_amortization(self, data: PolygonFinancialData) -> Optional[float]:
        """Estimate depreciation and amortization.
        
        Since this isn't directly available from Polygon, we estimate based on:
        1. Fixed assets as percentage (typically 8-15% annually)
        2. Industry standards
        """
        if data.fixed_assets and data.fixed_assets > 0:
            # Conservative estimate: 10% of fixed assets annually
            # For quarterly data, divide by 4
            annual_rate = 0.10
            if data.timeframe and data.timeframe.lower() == 'quarterly':
                return data.fixed_assets * annual_rate / 4
            else:
                return data.fixed_assets * annual_rate
        return None
    
    def _calculate_enhanced_free_cash_flow(self, data: PolygonFinancialData) -> Optional[float]:
        """Calculate free cash flow = Operating Cash Flow - Capital Expenditure."""
        if data.operating_cash_flow:
            capex = self._estimate_capital_expenditure(data)
            if capex:
                return data.operating_cash_flow - capex
            else:
                # If no CapEx estimate available, use operating cash flow as proxy
                return data.operating_cash_flow
        return None
    
    def _calculate_book_value_per_share(self, data: PolygonFinancialData) -> Optional[float]:
        """Calculate book value per share."""
        if data.total_equity and data.basic_shares and data.basic_shares > 0:
            return data.total_equity / data.basic_shares
        return None
    
    def _calculate_working_capital(self, data: PolygonFinancialData) -> Optional[float]:
        """Calculate working capital."""
        if data.current_assets and data.current_liabilities:
            return data.current_assets - data.current_liabilities
        return None
    
    def _calculate_revenue_per_share(self, data: PolygonFinancialData) -> Optional[float]:
        """Calculate revenue per share."""
        if data.revenues and data.basic_shares and data.basic_shares > 0:
            return data.revenues / data.basic_shares
        return None
    
    def _calculate_enhanced_free_cash_flow_per_share(self, data: PolygonFinancialData, fcf: Optional[float]) -> Optional[float]:
        """Calculate free cash flow per share using enhanced FCF."""
        if fcf and data.basic_shares and data.basic_shares > 0:
            return fcf / data.basic_shares
        return None
    
    def _calculate_gross_margin(self, data: PolygonFinancialData) -> Optional[float]:
        """Calculate gross margin."""
        if data.gross_profit and data.revenues and data.revenues > 0:
            return data.gross_profit / data.revenues
        return None
    
    def _calculate_operating_margin(self, data: PolygonFinancialData) -> Optional[float]:
        """Calculate operating margin."""
        if data.operating_income and data.revenues and data.revenues > 0:
            return data.operating_income / data.revenues
        return None
    
    def _calculate_net_margin(self, data: PolygonFinancialData) -> Optional[float]:
        """Calculate net margin."""
        if data.net_income and data.revenues and data.revenues > 0:
            return data.net_income / data.revenues
        return None
    
    def _calculate_current_ratio(self, data: PolygonFinancialData) -> Optional[float]:
        """Calculate current ratio."""
        if data.current_assets and data.current_liabilities and data.current_liabilities > 0:
            return data.current_assets / data.current_liabilities
        return None
    
    def _calculate_return_on_equity(self, data: PolygonFinancialData) -> Optional[float]:
        """Calculate return on equity."""
        if data.net_income and data.total_equity and data.total_equity > 0:
            return data.net_income / data.total_equity
        return None
    
    def _calculate_return_on_assets(self, data: PolygonFinancialData) -> Optional[float]:
        """Calculate return on assets."""
        if data.net_income and data.total_assets and data.total_assets > 0:
            return data.net_income / data.total_assets
        return None
    
    def _calculate_ebitda(self, data: PolygonFinancialData, depreciation: Optional[float]) -> Optional[float]:
        """Calculate EBITDA = EBIT + Depreciation & Amortization."""
        if data.operating_income and depreciation:
            return data.operating_income + depreciation
        return None

class PolygonFieldMappingService:
    """Service for managing Polygon financial data mappings"""
    
    def __init__(self):
        self.polygon_adapter = PolygonFinancialAdapter()
    
    def get_mappings_for_source(self, source: str, period_suffix: str) -> Dict[str, str]:
        """Get field mappings for a specific source"""
        if source == "polygon":
            return self.polygon_adapter.FIELD_MAPPINGS
        return {}
    
    def get_series_mapping(self, source: str, field_name: str, series_key: str) -> Optional[str]:
        """Get series mapping for a field"""
        if source == "polygon":
            return self.polygon_adapter.FIELD_MAPPINGS.get(field_name)
        return None 