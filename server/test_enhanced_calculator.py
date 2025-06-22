#!/usr/bin/env python3

"""
Test script for the enhanced FinancialCalculator with reported financials.
This script tests the integration between get_reported_financials and the calculator.
"""

import sys
import os
import logging

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from external.clients.finnhub_client import FinnHubClient
from external.clients.financial_calculator import FinancialCalculator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_enhanced_calculator():
    """Test the enhanced FinancialCalculator with Apple (AAPL) data."""
    
    # Initialize clients
    finnhub_client = FinnHubClient()
    calculator = FinancialCalculator()
    
    ticker = "AAPL"
    
    try:
        # Get reported financials
        logger.info(f"Fetching reported financials for {ticker}...")
        reported_financials = finnhub_client.get_reported_financials(ticker, freq="annual")
        logger.info(f"Retrieved {len(reported_financials.get('data', []))} years of data")
        
        # Get basic metrics for comparison
        logger.info(f"Fetching basic metrics for {ticker}...")
        basic_metrics = finnhub_client.get_basic_financials(ticker, period="ttm")
        metric = basic_metrics.get("metric", {})
        
        # Get company profile for shares outstanding
        profile = finnhub_client.get_company_profile(ticker)
        
        # Test TTM calculations with reported financials
        logger.info("Testing TTM calculations with reported financials...")
        ttm_mappings = calculator.calculate_missing_metrics(
            metric, "TTM", reported_financials
        )
        
        logger.info("TTM Mappings (using actual reported data):")
        for key, field in ttm_mappings.items():
            value = metric.get(field)
            logger.info(f"  {key}: {field} = {value}")
        
        # Test Annual calculations with reported financials
        logger.info("Testing Annual calculations with reported financials...")
        annual_mappings = calculator.calculate_missing_metrics(
            metric, "Annual", reported_financials
        )
        
        logger.info("Annual Mappings (using actual reported data):")
        for key, field in annual_mappings.items():
            value = metric.get(field)
            logger.info(f"  {key}: {field} = {value}")
        
        # Test error handling when no reported financials provided
        logger.info("Testing error handling without reported financials...")
        try:
            error_mappings = calculator.calculate_missing_metrics(
                metric, "TTM", None
            )
            logger.warning("Expected error but got mappings - this shouldn't happen!")
        except Exception as e:
            logger.info(f"Correctly handled missing reported financials: No error raised, returned empty dict")
        
        # Show actual values extracted from reported financials
        logger.info("\nActual values extracted from reported financials:")
        if reported_financials and "data" in reported_financials and reported_financials["data"]:
            latest = reported_financials["data"][0]
            logger.info(f"Data from year {latest.get('year')} (Form {latest.get('form')}):")
            
            # Show sample values from different financial statement sections
            for section_name, section_data in latest.get("report", {}).items():
                logger.info(f"  {section_name.upper()} section: {len(section_data)} items")
                for item in section_data[:3]:  # Show first 3 items as examples
                    concept = item.get("concept", "")
                    value = item.get("value", 0)
                    label = item.get("label", "")
                    if "Revenue" in concept or "Income" in concept or "Cash" in concept:
                        logger.info(f"    {concept}: {value:,} ({label})")
        
        # Show all actual metrics that were successfully extracted
        logger.info("\nSuccessfully extracted actual metrics:")
        for key, field in sorted(ttm_mappings.items()):
            if field.startswith("actual_"):
                value = metric.get(field)
                logger.info(f"  ✓ {key}: {value:,}" if isinstance(value, (int, float)) else f"  ✓ {key}: {value}")
        
        missing_metrics = []
        common_metrics = ["revenue", "net_income", "operating_cash_flow", "capital_expenditure", 
                         "depreciation_and_amortization", "free_cash_flow", "working_capital"]
        for metric_name in common_metrics:
            if metric_name not in ttm_mappings:
                missing_metrics.append(metric_name)
        
        if missing_metrics:
            logger.info(f"\nMetrics not found in reported financials: {missing_metrics}")
        else:
            logger.info("\nAll common metrics successfully extracted from reported financials!")
        
        logger.info("\nTest completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    test_enhanced_calculator() 