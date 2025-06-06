from typing import Dict, Optional, List
from abc import ABC, abstractmethod

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

class FieldMappingService:
    """Service to manage field mappings across different data sources."""
    
    def __init__(self):
        self.adapters = {
            "finnhub": FinnHubFieldAdapter()
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