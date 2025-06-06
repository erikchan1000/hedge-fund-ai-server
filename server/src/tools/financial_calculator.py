import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class FinancialCalculator:
    """Service for calculating missing financial metrics from available ratios and per-share data."""

    def __init__(self):
        # Industry average ratios for estimation
        self.INDUSTRY_AVERAGES = {
            "depreciation_as_pct_revenue": 0.05,  # 5% of revenue
            "capex_as_pct_revenue": 0.04,         # 4% of revenue
            "current_liabilities_as_pct_debt": 0.30,  # 30% of total debt
        }

    def calculate_missing_metrics(self, metric: Dict[str, Any], period_suffix: str) -> Dict[str, str]:
        """
        Calculate missing financial metrics and return field mappings.

        Args:
            metric: Dictionary of available financial metrics from API
            period_suffix: Either "TTM" or "Annual"

        Returns:
            Dictionary mapping line item names to calculated field names
        """
        logger.info(f"FinancialCalculator: Starting calculation for period {period_suffix}")
        calculated_mappings = {}
        logger.info(f"metric = {metric}")
        shares_outstanding = metric.get("shareOutstanding")
        logger.info(f"FinancialCalculator: shares_outstanding = {shares_outstanding}")

        if period_suffix == "TTM":
            calculated_mappings.update(self._calculate_ttm_metrics(metric, shares_outstanding))
        elif period_suffix == "Annual":
            calculated_mappings.update(self._calculate_annual_metrics(metric, shares_outstanding))

        logger.info(f"FinancialCalculator: Final mappings = {calculated_mappings}")
        return calculated_mappings

    def _calculate_ttm_metrics(self, metric: Dict[str, Any], shares_outstanding: Optional[float]) -> Dict[str, str]:
        """Calculate TTM-specific metrics."""
        logger.info(f"FinancialCalculator: Starting TTM metrics calculation")
        mappings = {}

        # Calculate free cash flow from EV/FCF ratio
        enterprise_value = metric.get("enterpriseValue")
        ev_fcf_ratio = metric.get("currentEv/freeCashFlowTTM")
        logger.info(f"FinancialCalculator: enterprise_value = {enterprise_value}, ev_fcf_ratio = {ev_fcf_ratio}")

        if enterprise_value and ev_fcf_ratio and ev_fcf_ratio > 0:
            calculated_fcf = enterprise_value / ev_fcf_ratio
            metric["calculated_from_ev_fcf"] = calculated_fcf
            mappings["free_cash_flow"] = "calculated_from_ev_fcf"
            logger.info(f"  Calculated free cash flow from EV/FCF: {calculated_fcf}")
        else:
            logger.warning(f"  Cannot calculate free cash flow: EV={enterprise_value}, EV/FCF={ev_fcf_ratio}")

        if shares_outstanding:
            logger.info(f"FinancialCalculator: shares_outstanding available: {shares_outstanding}")

            # Calculate net income from EPS
            eps_ttm = metric.get("epsBasicExclExtraItemsTTM")
            logger.info(f"FinancialCalculator: eps_ttm = {eps_ttm}")
            if eps_ttm:
                calculated_net_income = eps_ttm * shares_outstanding
                metric["calculated_net_income_ttm"] = calculated_net_income
                mappings["net_income"] = "calculated_net_income_ttm"
                logger.info(f"  Calculated net income from EPS * shares: {calculated_net_income}")
            else:
                logger.warning(f"  Cannot calculate net income: EPS TTM not available")

            # Calculate revenue from revenuePerShare
            revenue_per_share = metric.get("revenuePerShareTTM")
            logger.info(f"FinancialCalculator: revenue_per_share = {revenue_per_share}")
            if revenue_per_share:
                calculated_revenue = revenue_per_share * shares_outstanding
                metric["calculated_revenue_ttm"] = calculated_revenue
                mappings["revenue"] = "calculated_revenue_ttm"
                logger.info(f"  Calculated revenue from revenuePerShare * shares: {calculated_revenue}")

                # Estimate depreciation and amortization as % of revenue
                estimated_da = calculated_revenue * self.INDUSTRY_AVERAGES["depreciation_as_pct_revenue"]
                metric["estimated_da_ttm"] = estimated_da
                mappings["depreciation_and_amortization"] = "estimated_da_ttm"
                logger.info(f"  Estimated depreciation & amortization (5% of revenue): {estimated_da}")
            else:
                logger.warning(f"  Cannot calculate revenue: revenuePerShare TTM not available")

            # Calculate operating cash flow from cashFlowPerShare
            cash_flow_per_share = metric.get("cashFlowPerShareTTM")
            logger.info(f"FinancialCalculator: cash_flow_per_share = {cash_flow_per_share}")
            if cash_flow_per_share:
                calculated_ocf = cash_flow_per_share * shares_outstanding
                metric["calculated_operating_cf_ttm"] = calculated_ocf
                mappings["operating_cash_flow"] = "calculated_operating_cf_ttm"
                logger.info(f"  Calculated operating cash flow from cashFlowPerShare * shares: {calculated_ocf}")

                # Calculate capital expenditure from OCF - FCF if both available
                calculated_fcf = metric.get("calculated_from_ev_fcf")
                if calculated_fcf:
                    estimated_capex = calculated_ocf - calculated_fcf
                    if self._is_reasonable_capex(estimated_capex, calculated_ocf):
                        metric["estimated_capex_ttm"] = estimated_capex
                        mappings["capital_expenditure"] = "estimated_capex_ttm"
                        mappings["capital_expenditures"] = "estimated_capex_ttm"
                        logger.info(f"  Estimated capital expenditure (OCF - FCF): {estimated_capex}")
                    else:
                        # Fall back to revenue-based estimate
                        revenue = metric.get("calculated_revenue_ttm")
                        if revenue:
                            estimated_capex = revenue * self.INDUSTRY_AVERAGES["capex_as_pct_revenue"]
                            metric["estimated_capex_revenue_ttm"] = estimated_capex
                            mappings["capital_expenditure"] = "estimated_capex_revenue_ttm"
                            mappings["capital_expenditures"] = "estimated_capex_revenue_ttm"
                            logger.info(f"  Estimated capital expenditure (4% of revenue): {estimated_capex}")
            else:
                logger.warning(f"  Cannot calculate operating cash flow: cashFlowPerShare TTM not available")

            # Estimate capital expenditure from revenue if OCF method didn't work
            revenue = metric.get("calculated_revenue_ttm")
            if revenue and "capital_expenditure" not in mappings:
                estimated_capex = revenue * self.INDUSTRY_AVERAGES["capex_as_pct_revenue"]
                metric["estimated_capex_revenue_ttm"] = estimated_capex
                mappings["capital_expenditure"] = "estimated_capex_revenue_ttm"
                mappings["capital_expenditures"] = "estimated_capex_revenue_ttm"
                logger.info(f"  Estimated capital expenditure (4% of revenue): {estimated_capex}")
        else:
            logger.warning(f"FinancialCalculator: shares_outstanding not available, skipping per-share calculations")

        # Estimate working capital using balance sheet ratios
        working_capital = self._estimate_working_capital(metric, "TTM")
        if working_capital is not None:
            metric["calculated_working_capital_ttm"] = working_capital
            mappings["working_capital"] = "calculated_working_capital_ttm"
            logger.info(f"  Estimated working capital: {working_capital}")

        logger.info(f"FinancialCalculator: TTM mappings = {mappings}")
        return mappings

    def _calculate_annual_metrics(self, metric: Dict[str, Any], shares_outstanding: Optional[float]) -> Dict[str, str]:
        """Calculate Annual-specific metrics."""
        mappings = {}

        if shares_outstanding:
            # Calculate net income from EPS
            eps_annual = metric.get("epsBasicExclExtraItemsAnnual")
            if eps_annual:
                calculated_net_income = eps_annual * shares_outstanding
                metric["calculated_net_income_annual"] = calculated_net_income
                mappings["net_income"] = "calculated_net_income_annual"
                logger.info(f"  Calculated annual net income from EPS * shares: {calculated_net_income}")

            # Calculate revenue from revenuePerShare
            revenue_per_share = metric.get("revenuePerShareAnnual")
            if revenue_per_share:
                calculated_revenue = revenue_per_share * shares_outstanding
                metric["calculated_revenue_annual"] = calculated_revenue
                mappings["revenue"] = "calculated_revenue_annual"
                logger.info(f"  Calculated annual revenue from revenuePerShare * shares: {calculated_revenue}")

                # Estimate depreciation and amortization as % of revenue
                estimated_da = calculated_revenue * self.INDUSTRY_AVERAGES["depreciation_as_pct_revenue"]
                metric["estimated_da_annual"] = estimated_da
                mappings["depreciation_and_amortization"] = "estimated_da_annual"
                logger.info(f"  Estimated annual depreciation & amortization (5% of revenue): {estimated_da}")

                # Estimate capital expenditure as % of revenue
                estimated_capex = calculated_revenue * self.INDUSTRY_AVERAGES["capex_as_pct_revenue"]
                metric["estimated_capex_annual"] = estimated_capex
                mappings["capital_expenditure"] = "estimated_capex_annual"
                mappings["capital_expenditures"] = "estimated_capex_annual"
                logger.info(f"  Estimated annual capital expenditure (4% of revenue): {estimated_capex}")

            # Calculate operating cash flow from cashFlowPerShare
            cash_flow_per_share = metric.get("cashFlowPerShareAnnual")
            if cash_flow_per_share:
                calculated_ocf = cash_flow_per_share * shares_outstanding
                metric["calculated_operating_cf_annual"] = calculated_ocf
                mappings["operating_cash_flow"] = "calculated_operating_cf_annual"
                logger.info(f"  Calculated annual operating cash flow from cashFlowPerShare * shares: {calculated_ocf}")

        return mappings

    def _estimate_working_capital(self, metric: Dict[str, Any], period_suffix: str) -> Optional[float]:
        """
        Estimate working capital using current ratio and balance sheet approximations.

        This is a rough estimation and should be used only when direct data is unavailable.
        """
        current_ratio = metric.get("currentRatioAnnual") or metric.get("currentRatioQuarterly")
        total_debt_to_equity = metric.get("totalDebt/totalEquityAnnual") or metric.get("totalDebt/totalEquityQuarterly")
        market_cap = metric.get("marketCapitalization")
        pb_ratio = metric.get("pbAnnual") or metric.get("pbQuarterly")

        if not all([current_ratio, market_cap, pb_ratio]) or pb_ratio <= 0:
            return None

        try:
            # Estimate book value from market cap and P/B ratio
            estimated_book_value = market_cap / pb_ratio

            if total_debt_to_equity and total_debt_to_equity > 0:
                # Estimate total debt
                estimated_total_debt = total_debt_to_equity * estimated_book_value

                # Rough approximation: current liabilities ≈ 30% of total debt
                estimated_current_liabilities = estimated_total_debt * self.INDUSTRY_AVERAGES["current_liabilities_as_pct_debt"]

                # Current assets = current ratio × current liabilities
                estimated_current_assets = current_ratio * estimated_current_liabilities

                # Working capital = current assets - current liabilities
                working_capital = estimated_current_assets - estimated_current_liabilities

                return working_capital
        except (TypeError, ZeroDivisionError):
            return None

        return None

    def _is_reasonable_capex(self, capex: float, operating_cf: float) -> bool:
        """
        Check if calculated capex seems reasonable.

        Capex should be positive and typically less than 50% of operating cash flow.
        """
        if capex <= 0:
            return False
        if operating_cf > 0 and capex > operating_cf * 0.5:
            return False
        return True
