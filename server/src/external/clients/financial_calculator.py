import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class FinancialCalculator:
    """Service for extracting financial metrics from reported financials data."""

    def __init__(self):
        # GAAP concept mappings for reported financials
        self.GAAP_MAPPINGS = {
            "revenue": [
                "us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax",
                "us-gaap_SalesRevenueNet", 
                "us-gaap_Revenues"
            ],
            "net_income": ["us-gaap_NetIncomeLoss"],
            "operating_cash_flow": ["us-gaap_NetCashProvidedByUsedInOperatingActivities"],
            "capital_expenditure": [
                "us-gaap_PaymentsToAcquirePropertyPlantAndEquipment",
                "us-gaap_PaymentsToAcquireProductiveAssets"
            ],
            "depreciation_and_amortization": [
                "us-gaap_DepreciationDepletionAndAmortization",
                "us-gaap_DepreciationAmortizationAndAccretionNet"
            ],
            "current_assets": ["us-gaap_AssetsCurrent"],
            "current_liabilities": ["us-gaap_LiabilitiesCurrent"],
            "total_assets": ["us-gaap_Assets"],
            "total_liabilities": ["us-gaap_Liabilities"],
            "gross_profit": ["us-gaap_GrossProfit"],
            "operating_income": ["us-gaap_OperatingIncomeLoss"],
            "cost_of_goods_sold": ["us-gaap_CostOfGoodsAndServicesSold"],
            "research_and_development": ["us-gaap_ResearchAndDevelopmentExpense"],
            "selling_general_administrative": ["us-gaap_SellingGeneralAndAdministrativeExpense"],
            "accounts_receivable": [
                "us-gaap_AccountsReceivableNetCurrent",
                "us-gaap_AccountsReceivableNet"
            ],
            "inventory": ["us-gaap_InventoryNet"],
            "accounts_payable": ["us-gaap_AccountsPayableCurrent"],
            "cash_and_equivalents": ["us-gaap_CashAndCashEquivalentsAtCarryingValue"],
            "shares_outstanding": [
                "us-gaap_WeightedAverageNumberOfSharesOutstandingBasic",
                "us-gaap_CommonStockSharesOutstanding"
            ],
            "ebitda": ["us-gaap_EarningsBeforeInterestTaxesDepreciationAndAmortization"],
            "ebit": ["us-gaap_OperatingIncomeLoss"],  # Operating income is essentially EBIT
            "interest_expense": ["us-gaap_InterestExpense"],
            "income_tax_expense": ["us-gaap_IncomeTaxExpenseBenefit"],
            "free_cash_flow": None,  # Calculated as operating_cash_flow - capital_expenditure
            "working_capital": None,  # Calculated as current_assets - current_liabilities
        }

    def calculate_missing_metrics(self, metric: Dict[str, Any], period_suffix: str, 
                                reported_financials: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract financial metrics from reported financials data.

        Args:
            metric: Dictionary to store calculated values
            period_suffix: Either "TTM" or "Annual" 
            reported_financials: Required reported financials data from get_reported_financials

        Returns:
            Dictionary mapping line item names to field names in metric dict
        """
        logger.info(f"FinancialCalculator: Starting extraction for period {period_suffix}")
        
        if not reported_financials or "data" not in reported_financials or not reported_financials["data"]:
            logger.error("FinancialCalculator: No reported financials data provided")
            return {}

        mappings = {}
        
        # Get the most recent financial data
        latest_financials = self._get_latest_financials(reported_financials["data"])
        if not latest_financials:
            logger.error("FinancialCalculator: No valid financial data found")
            return {}
            
        logger.info(f"FinancialCalculator: Using reported financials from {latest_financials.get('year')}")

        # Extract actual values from reported financials
        mappings.update(self._extract_actual_metrics(metric, latest_financials, period_suffix))

        logger.info(f"FinancialCalculator: Final mappings = {mappings}")
        return mappings

    def _get_latest_financials(self, financial_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get the most recent financial data from reported financials."""
        if not financial_data:
            return {}
        
        # Sort by year descending to get the latest
        sorted_data = sorted(financial_data, key=lambda x: x.get("year", 0), reverse=True)
        return sorted_data[0] if sorted_data else {}

    def _extract_value_from_financials(self, financials: Dict[str, Any], metric_type: str) -> float:
        """Extract a specific metric value from reported financials."""
        if not financials or "report" not in financials:
            return None

        concepts = self.GAAP_MAPPINGS.get(metric_type, [])
        if not concepts:
            return None
        
        # Search through all financial statement sections (bs, ic, cf)
        for section_name in ["bs", "ic", "cf"]:
            section = financials["report"].get(section_name, [])
            for item in section:
                if item.get("concept") in concepts:
                    value = item.get("value")
                    if value is not None:
                        logger.info(f"Found {metric_type}: {value} from concept {item.get('concept')}")
                        return float(value)
        
        return None

    def _extract_actual_metrics(self, metric: Dict[str, Any], reported_financials: Dict[str, Any], 
                              period_suffix: str) -> Dict[str, str]:
        """Extract actual metrics from reported financials only."""
        logger.info(f"FinancialCalculator: Extracting actual metrics for {period_suffix}")
        mappings = {}

        actual_revenue = self._extract_value_from_financials(reported_financials, "revenue")
        if actual_revenue is not None:
            field_name = f"actual_revenue_{period_suffix.lower()}"
            metric[field_name] = actual_revenue
            mappings["revenue"] = field_name
            logger.info(f"  Using actual revenue: {actual_revenue}")

        actual_net_income = self._extract_value_from_financials(reported_financials, "net_income")
        if actual_net_income is not None:
            field_name = f"actual_net_income_{period_suffix.lower()}"
            metric[field_name] = actual_net_income
            mappings["net_income"] = field_name
            logger.info(f"  Using actual net income: {actual_net_income}")

        actual_ocf = self._extract_value_from_financials(reported_financials, "operating_cash_flow")
        if actual_ocf is not None:
            field_name = f"actual_operating_cf_{period_suffix.lower()}"
            metric[field_name] = actual_ocf
            mappings["operating_cash_flow"] = field_name
            logger.info(f"  Using actual operating cash flow: {actual_ocf}")

        actual_capex = self._extract_value_from_financials(reported_financials, "capital_expenditure")
        if actual_capex is not None:
            actual_capex = abs(actual_capex)
            field_name = f"actual_capex_{period_suffix.lower()}"
            metric[field_name] = actual_capex
            mappings["capital_expenditure"] = field_name
            mappings["capital_expenditures"] = field_name
            logger.info(f"  Using actual capital expenditure: {actual_capex}")

        actual_da = self._extract_value_from_financials(reported_financials, "depreciation_and_amortization")
        if actual_da is not None:
            field_name = f"actual_da_{period_suffix.lower()}"
            metric[field_name] = actual_da
            mappings["depreciation_and_amortization"] = field_name
            logger.info(f"  Using actual depreciation & amortization: {actual_da}")

        actual_current_assets = self._extract_value_from_financials(reported_financials, "current_assets")
        if actual_current_assets is not None:
            field_name = f"actual_current_assets_{period_suffix.lower()}"
            metric[field_name] = actual_current_assets
            mappings["current_assets"] = field_name
            logger.info(f"  Using actual current assets: {actual_current_assets}")

        actual_current_liabilities = self._extract_value_from_financials(reported_financials, "current_liabilities")
        if actual_current_liabilities is not None:
            field_name = f"actual_current_liabilities_{period_suffix.lower()}"
            metric[field_name] = actual_current_liabilities
            mappings["current_liabilities"] = field_name
            logger.info(f"  Using actual current liabilities: {actual_current_liabilities}")

        actual_total_assets = self._extract_value_from_financials(reported_financials, "total_assets")
        if actual_total_assets is not None:
            field_name = f"actual_total_assets_{period_suffix.lower()}"
            metric[field_name] = actual_total_assets
            mappings["total_assets"] = field_name
            logger.info(f"  Using actual total assets: {actual_total_assets}")

        actual_total_liabilities = self._extract_value_from_financials(reported_financials, "total_liabilities")
        if actual_total_liabilities is not None:
            field_name = f"actual_total_liabilities_{period_suffix.lower()}"
            metric[field_name] = actual_total_liabilities
            mappings["total_liabilities"] = field_name
            logger.info(f"  Using actual total liabilities: {actual_total_liabilities}")

        # Gross profit from reported financials
        actual_gross_profit = self._extract_value_from_financials(reported_financials, "gross_profit")
        if actual_gross_profit is not None:
            field_name = f"actual_gross_profit_{period_suffix.lower()}"
            metric[field_name] = actual_gross_profit
            mappings["gross_profit"] = field_name
            logger.info(f"  Using actual gross profit: {actual_gross_profit}")

        actual_operating_income = self._extract_value_from_financials(reported_financials, "operating_income")
        if actual_operating_income is not None:
            field_name = f"actual_operating_income_{period_suffix.lower()}"
            metric[field_name] = actual_operating_income
            mappings["operating_income"] = field_name
            mappings["ebit"] = field_name  # Operating income is essentially EBIT
            logger.info(f"  Using actual operating income/EBIT: {actual_operating_income}")

        actual_cogs = self._extract_value_from_financials(reported_financials, "cost_of_goods_sold")
        if actual_cogs is not None:
            field_name = f"actual_cogs_{period_suffix.lower()}"
            metric[field_name] = actual_cogs
            mappings["cost_of_goods_sold"] = field_name
            logger.info(f"  Using actual cost of goods sold: {actual_cogs}")

        actual_rd = self._extract_value_from_financials(reported_financials, "research_and_development")
        if actual_rd is not None:
            field_name = f"actual_rd_{period_suffix.lower()}"
            metric[field_name] = actual_rd
            mappings["research_and_development"] = field_name
            logger.info(f"  Using actual R&D: {actual_rd}")

        actual_ar = self._extract_value_from_financials(reported_financials, "accounts_receivable")
        if actual_ar is not None:
            field_name = f"actual_accounts_receivable_{period_suffix.lower()}"
            metric[field_name] = actual_ar
            mappings["accounts_receivable"] = field_name
            logger.info(f"  Using actual accounts receivable: {actual_ar}")

        actual_inventory = self._extract_value_from_financials(reported_financials, "inventory")
        if actual_inventory is not None:
            field_name = f"actual_inventory_{period_suffix.lower()}"
            metric[field_name] = actual_inventory
            mappings["inventory"] = field_name
            logger.info(f"  Using actual inventory: {actual_inventory}")

        actual_ap = self._extract_value_from_financials(reported_financials, "accounts_payable")
        if actual_ap is not None:
            field_name = f"actual_accounts_payable_{period_suffix.lower()}"
            metric[field_name] = actual_ap
            mappings["accounts_payable"] = field_name
            logger.info(f"  Using actual accounts payable: {actual_ap}")

        # Cash and equivalents from reported financials
        actual_cash = self._extract_value_from_financials(reported_financials, "cash_and_equivalents")
        if actual_cash is not None:
            field_name = f"actual_cash_{period_suffix.lower()}"
            metric[field_name] = actual_cash
            mappings["cash_and_equivalents"] = field_name
            logger.info(f"  Using actual cash and equivalents: {actual_cash}")

        # Calculate derived metrics from actual values only
        # Free cash flow = Operating cash flow - Capital expenditure
        if actual_ocf is not None and actual_capex is not None:
            actual_fcf = actual_ocf - actual_capex
            field_name = f"actual_fcf_{period_suffix.lower()}"
            metric[field_name] = actual_fcf
            mappings["free_cash_flow"] = field_name
            logger.info(f"  Calculated actual free cash flow: {actual_fcf}")

        if actual_current_assets is not None and actual_current_liabilities is not None:
            actual_working_capital = actual_current_assets - actual_current_liabilities
            field_name = f"actual_working_capital_{period_suffix.lower()}"
            metric[field_name] = actual_working_capital
            mappings["working_capital"] = field_name
            logger.info(f"  Calculated actual working capital: {actual_working_capital}")

        return mappings 