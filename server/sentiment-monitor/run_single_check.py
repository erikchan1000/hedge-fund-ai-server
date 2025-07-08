#!/usr/bin/env python3
"""
Single Check Runner for Sentiment Monitoring

This script runs a single sentiment monitoring cycle and exits.
It's designed to be called by system cron or other external schedulers.
"""

import os
import sys
import asyncio
from datetime import datetime
from loguru import logger
from sentiment_service import SentimentMonitorService


async def main():
    """Run a single sentiment monitoring check."""
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    # Configure minimal logging for cron execution
    logger.remove()
    logger.add(
        "logs/cron_{time:YYYY-MM-DD}.log",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        rotation="1 day",
        retention="30 days"
    )
    
    start_time = datetime.now()
    logger.info(f"Starting single sentiment check at {start_time}")
    
    try:
        # Initialize service
        service = SentimentMonitorService("config.yml")
        
        # Run monitoring cycle
        await service.run_monitoring_cycle()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Single sentiment check completed successfully in {duration:.2f} seconds")
        
        # Exit with success code
        sys.exit(0)
        
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.error(f"Single sentiment check failed after {duration:.2f} seconds: {e}")
        
        # Exit with error code
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 