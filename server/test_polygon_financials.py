#!/usr/bin/env python3
"""
Test script for Polygon.io client financial data methods.
This script tests the actual API calls to ensure the client works correctly.
"""

import logging
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from external.clients.polygon_client import PolygonClient
from external.clients.api import search_line_items

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_polygon_financials():
    """Test Polygon.io financial data methods."""
    
    # Initialize client
    try:
        client = PolygonClient()
        logger.info("✅ PolygonClient initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize PolygonClient: {e}")
        return False
    # Test ticker - using AAPL as it should have good financial data
    test_ticker = "AAPL"
    logger.info(f"Testing with ticker: {test_ticker}")
    
    # Test 2: Basic Financials
    logger.info("\n" + "="*50)
    logger.info("TEST 2: get_basic_financials()")
    logger.info("="*50)
    
    try:
        basic_financials = client.get_basic_financials(test_ticker, period="ttm", limit=10)
        logger.info(f"✅ Basic financials retrieved successfully")
        
        metrics = basic_financials.get("metric", {})
        series = basic_financials.get("series", {})
        
        logger.info(f"Number of metrics: {len(metrics)}")
        logger.info(f"Series sections: {list(series.keys())}")
        
        # Log some key metrics if available
        key_metrics = [
            "marketCapitalization", "revenuePerShareTTM", "epsBasicExclExtraItemsTTM",
            "peTTM", "pbTTM", "roeTTM", "roaTTM", "currentRatioTTM"
        ]
        
        logger.info("Key metrics found:")
        for metric_name in key_metrics:
            value = metrics.get(metric_name)
            if value is not None:
                logger.info(f"  {metric_name}: {value}")
        
        # Basic assertions
        assert isinstance(metrics, dict), "Metrics should be a dictionary"
        assert isinstance(series, dict), "Series should be a dictionary"
        
    except Exception as e:
        logger.error(f"❌ get_basic_financials() failed: {e}")
        return False
    


    # Test 1: Company Profile
    logger.info("\n" + "="*50)
    logger.info("TEST 1: get_company_profile()")
    logger.info("="*50)
    
    try:
        profile = client.get_company_profile(test_ticker)
        logger.info(f"✅ Company profile retrieved successfully")
        logger.info(f"Company name: {profile.get('name', 'N/A')}")
        logger.info(f"Market cap: {profile.get('marketCapitalization', 'N/A')}")
        logger.info(f"Shares outstanding: {profile.get('shareOutstanding', 'N/A')}")
        logger.info(f"Currency: {profile.get('currency', 'N/A')}")
        
        # Basic assertions
        assert profile.get('name'), "Company name should not be empty"
        assert profile.get('ticker') == test_ticker, f"Ticker should be {test_ticker}"
        
    except Exception as e:
        logger.error(f"❌ get_company_profile() failed: {e}")
        return False
    
    # Test 3: Reported Financials
    logger.info("\n" + "="*50)
    logger.info("TEST 3: get_reported_financials()")
    logger.info("="*50)
    
    try:
        reported_financials = client.get_reported_financials(test_ticker, freq="annual")
        logger.info(f"✅ Reported financials retrieved successfully")
        logger.info(f"Number of financial periods: {len(reported_financials)}")
        
        if reported_financials:
            # Examine the most recent financial data
            latest = reported_financials[0]
            logger.info(f"Latest financial data:")
            logger.info(f"  Fiscal year: {getattr(latest, 'fiscal_year', 'N/A')}")
            logger.info(f"  Fiscal quarter: {getattr(latest, 'fiscal_quarter', 'N/A')}")
            logger.info(f"  Period: {getattr(latest, 'period_of_report_date', 'N/A')}")
            
            # Check if financials data exists
            financials_data = getattr(latest, 'financials', {})
            if financials_data:
                logger.info(f"  Financial sections available: {list(financials_data.keys())}")
                
                # Check for common financial statement sections
                for section in ['balance_sheet', 'income_statement', 'cash_flow_statement']:
                    if section in financials_data:
                        section_data = financials_data[section]
                        logger.info(f"    {section}: {len(section_data) if isinstance(section_data, list) else 'Available'}")
            else:
                logger.warning("  No financials data found in latest period")
        
        # Basic assertions
        assert isinstance(reported_financials, list), "Reported financials should be a list"
        
    except Exception as e:
        logger.error(f"❌ get_reported_financials() failed: {e}")
        return False
    
    # Test 4: Stock Price (quick test)
    logger.info("\n" + "="*50)
    logger.info("TEST 4: get_stock_price()")
    logger.info("="*50)
    
    try:
        # Test with a short date range to avoid too much data
        price_data = client.get_stock_price(test_ticker, "2024-01-01", "2024-01-05")
        logger.info(f"✅ Stock price data retrieved successfully")
        
        if price_data.get("s") == "ok":
            timestamps = price_data.get("t", [])
            closes = price_data.get("c", [])
            logger.info(f"Number of price points: {len(timestamps)}")
            if closes:
                logger.info(f"Sample closing price: ${closes[0]}")
        else:
            logger.warning(f"Price data status: {price_data.get('s', 'unknown')}")
        
        # Basic assertions
        assert "s" in price_data, "Price data should have status field"
        
    except Exception as e:
        logger.error(f"❌ get_stock_price() failed: {e}")
        return False
    
    # Test 5: Search Line Items
    logger.info("\n" + "="*50)
    logger.info("TEST 5: search_line_items()")
    logger.info("="*50)
    
    try:
        # Test with common financial line items
        test_line_items = [
            "revenue",
            "net_income", 
            "total_assets",
            "current_assets",
            "current_liabilities",
            "shares_outstanding",
            "earnings_per_share",
            "book_value_per_share"
        ]
        
        line_items_result = search_line_items(
            ticker=test_ticker,
            line_items=test_line_items,
            end_date="2024-12-31",
            period="ttm",
            limit=5
        )
        
        logger.info(f"✅ Search line items retrieved successfully")
        logger.info(f"Number of line items found: {len(line_items_result)}")
        
        # Log details about found line items
        if line_items_result:
            logger.info("Found line items:")
            for item in line_items_result:
                logger.info(f"  {item.name}: {item.value} ({item.currency}) - Period: {item.report_period} - Source: {item.source}")
        
        # Test assertions
        assert isinstance(line_items_result, list), "search_line_items should return a list"
        
        # Check that we found at least some line items
        if line_items_result:
            first_item = line_items_result[0]
            assert hasattr(first_item, 'ticker'), "LineItem should have ticker attribute"
            assert hasattr(first_item, 'name'), "LineItem should have name attribute"
            assert hasattr(first_item, 'value'), "LineItem should have value attribute"
            assert hasattr(first_item, 'report_period'), "LineItem should have report_period attribute"
            assert hasattr(first_item, 'currency'), "LineItem should have currency attribute"
            assert first_item.ticker == test_ticker, f"Ticker should be {test_ticker}"
            assert first_item.value is not None, "Value should not be None"
            logger.info(f"✅ Line item structure validation passed")
        else:
            logger.warning("⚠️ No line items found - this might be expected if data is not available")
        
    except Exception as e:
        logger.error(f"❌ search_line_items() failed: {e}")
        return False
    
    logger.info("\n" + "="*50)
    logger.info("🎉 ALL TESTS PASSED!")
    logger.info("="*50)
    return True

def test_search_line_items_detailed():
    """Test search_line_items function with various scenarios."""
    logger.info("\n" + "="*50)
    logger.info("DETAILED TEST: search_line_items()")
    logger.info("="*50)
    
    test_ticker = "AAPL"
    
    # Test 1: Common line items that should exist
    logger.info("\nTest 1: Common financial line items")
    try:
        common_items = ["revenue", "net_income", "total_assets", "shares_outstanding"]
        results = search_line_items(
            ticker=test_ticker,
            line_items=common_items,
            end_date="2024-12-31",
            period="ttm",
            limit=10
        )
        
        logger.info(f"Found {len(results)} line items for common request")
        for item in results:
            logger.info(f"  - {item.name}: {item.value:,.2f} {item.currency}")
        
        assert len(results) > 0, "Should find at least some common line items"
        
    except Exception as e:
        logger.error(f"❌ Common line items test failed: {e}")
        return False
    
    # Test 2: Per-share metrics
    logger.info("\nTest 2: Per-share metrics")
    try:
        per_share_items = ["earnings_per_share", "book_value_per_share", "revenue_per_share"]
        results = search_line_items(
            ticker=test_ticker,
            line_items=per_share_items,
            end_date="2024-12-31",
            period="ttm",
            limit=5
        )
        
        logger.info(f"Found {len(results)} per-share metrics")
        for item in results:
            logger.info(f"  - {item.name}: ${item.value:.2f} per share")
            
    except Exception as e:
        logger.error(f"❌ Per-share metrics test failed: {e}")
        return False
    
    # Test 3: Balance sheet items
    logger.info("\nTest 3: Balance sheet items")
    try:
        balance_sheet_items = ["current_assets", "current_liabilities", "total_debt", "cash_and_equivalents"]
        results = search_line_items(
            ticker=test_ticker,
            line_items=balance_sheet_items,
            end_date="2024-12-31",
            period="annual",
            limit=3
        )
        
        logger.info(f"Found {len(results)} balance sheet items")
        for item in results:
            logger.info(f"  - {item.name}: ${item.value:,.0f} ({item.period})")
            
    except Exception as e:
        logger.error(f"❌ Balance sheet items test failed: {e}")
        return False
    
    # Test 4: Invalid ticker (error handling)
    logger.info("\nTest 4: Error handling with invalid ticker")
    try:
        results = search_line_items(
            ticker="INVALID_TICKER_XYZ",
            line_items=["revenue"],
            end_date="2024-12-31",
            period="ttm",
            limit=1
        )
        logger.info(f"Invalid ticker returned {len(results)} results (expected behavior)")
        
    except Exception as e:
        logger.info(f"Expected error for invalid ticker: {str(e)[:100]}...")
    
    # Test 5: Non-existent line items
    logger.info("\nTest 5: Non-existent line items")
    try:
        fake_items = ["nonexistent_metric", "fake_line_item", "imaginary_value"]
        results = search_line_items(
            ticker=test_ticker,
            line_items=fake_items,
            end_date="2024-12-31",
            period="ttm",
            limit=5
        )
        
        logger.info(f"Non-existent line items returned {len(results)} results")
        if results:
            logger.warning("⚠️ Unexpected: Found results for non-existent line items")
        else:
            logger.info("✅ Correctly returned no results for non-existent line items")
            
    except Exception as e:
        logger.error(f"Non-existent line items test failed: {e}")
        return False
    
    logger.info("\n✅ All search_line_items detailed tests completed!")
    return True

def test_rate_limiting():
    """Test that rate limiting works properly."""
    logger.info("\n" + "="*50)
    logger.info("TEST: Rate Limiting")
    logger.info("="*50)
    
    try:
        client = PolygonClient()
        
        # Make multiple quick requests to test rate limiting
        logger.info("Making 3 consecutive requests to test rate limiting...")
        
        start_time = time.time()
        for i in range(3):
            logger.info(f"Request {i+1}/3...")
            profile = client.get_company_profile("AAPL")
            assert profile.get('name'), f"Request {i+1} should return valid data"
        
        end_time = time.time()
        total_time = end_time - start_time
        
        logger.info(f"✅ Rate limiting test completed in {total_time:.2f} seconds")
        
        # Should take at least 4 seconds (2 seconds between each of the 3 requests)
        expected_min_time = 4.0
        if total_time >= expected_min_time:
            logger.info(f"✅ Rate limiting working properly (took {total_time:.2f}s, expected >= {expected_min_time}s)")
        else:
            logger.warning(f"⚠️ Rate limiting may not be working (took {total_time:.2f}s, expected >= {expected_min_time}s)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Rate limiting test failed: {e}")
        return False

if __name__ == "__main__":
    import time
    
    logger.info("Starting Polygon.io Financial Data Tests")
    logger.info("="*60)
    
    # Run financial tests
    success = test_polygon_financials()
    
    if success:
        # Run detailed search_line_items test
        success = test_search_line_items_detailed()
    
    if success:
        # Run rate limiting test
        success = test_rate_limiting()
    
    if success:
        logger.info("\n🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        logger.error("\n❌ Some tests failed!")
        sys.exit(1) 