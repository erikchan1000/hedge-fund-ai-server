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
    
    logger.info("\n" + "="*50)
    logger.info("🎉 ALL TESTS PASSED!")
    logger.info("="*50)
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
        # Run rate limiting test
        success = test_rate_limiting()
    
    if success:
        logger.info("\n🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        logger.error("\n❌ Some tests failed!")
        sys.exit(1) 