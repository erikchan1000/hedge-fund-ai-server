#!/usr/bin/env python3
"""
Cron Scheduler for Sentiment Monitoring Service

This module provides different ways to schedule the sentiment monitoring service:
1. Using the schedule library for Python-based scheduling
2. Using system cron for production deployments
3. Manual execution for testing
"""

import os
import sys
import time
import asyncio
import schedule
from datetime import datetime
from loguru import logger
from sentiment_service import SentimentMonitorService


class CronScheduler:
    """Handles scheduling of sentiment monitoring tasks."""
    
    def __init__(self, config_path: str = "config.yml"):
        self.service = SentimentMonitorService(config_path)
        self.is_running = False
        logger.info("Cron scheduler initialized")
    
    async def run_single_check(self):
        """Run a single monitoring cycle."""
        logger.info("Starting scheduled sentiment monitoring cycle")
        try:
            await self.service.run_monitoring_cycle()
            logger.info("Scheduled monitoring cycle completed successfully")
        except Exception as e:
            logger.error(f"Error in scheduled monitoring cycle: {e}")
    
    def job_wrapper(self):
        """Wrapper to run async job in sync context."""
        try:
            asyncio.run(self.run_single_check())
        except Exception as e:
            logger.error(f"Job wrapper error: {e}")
    
    def start_python_scheduler(self, interval_minutes: int = 60):
        """Start Python-based scheduler using the schedule library."""
        logger.info(f"Starting Python scheduler (every {interval_minutes} minutes)")
        
        # Schedule the job
        schedule.every(interval_minutes).minutes.do(self.job_wrapper)
        
        # Run initial check
        logger.info("Running initial monitoring cycle")
        self.job_wrapper()
        
        # Main scheduler loop
        self.is_running = True
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute for pending jobs
        except KeyboardInterrupt:
            logger.info("Scheduler interrupted by user")
            self.stop()
    
    def stop(self):
        """Stop the scheduler."""
        self.is_running = False
        logger.info("Scheduler stopped")
    
    def generate_crontab_entry(self, interval_minutes: int = 60) -> str:
        """Generate crontab entry for system cron."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        python_path = sys.executable
        
        if interval_minutes == 60:
            # Every hour
            cron_time = "0 * * * *"
        elif interval_minutes == 30:
            # Every 30 minutes
            cron_time = "*/30 * * * *"
        elif interval_minutes == 15:
            # Every 15 minutes
            cron_time = "*/15 * * * *"
        else:
            # Custom interval (approximated)
            cron_time = f"*/{interval_minutes} * * * *"
        
        cron_entry = f"{cron_time} cd {script_dir} && {python_path} run_single_check.py >> logs/cron.log 2>&1"
        return cron_entry
    
    def install_crontab(self, interval_minutes: int = 60):
        """Install crontab entry for this service."""
        cron_entry = self.generate_crontab_entry(interval_minutes)
        
        print("To install this service with system cron, add the following line to your crontab:")
        print("(Run 'crontab -e' to edit your crontab)")
        print()
        print(cron_entry)
        print()
        print("For logs, check the logs/cron.log file")
    
    async def test_service(self):
        """Test the service connectivity and configuration."""
        logger.info("Testing sentiment monitoring service...")
        
        # Test database connection
        try:
            with self.service.get_db_session() as db:
                logger.info("✓ Database connection successful")
        except Exception as e:
            logger.error(f"✗ Database connection failed: {e}")
            return False
        
        # Test Redis connection
        if self.service.redis_client:
            try:
                self.service.redis_client.ping()
                logger.info("✓ Redis connection successful")
            except Exception as e:
                logger.warning(f"✗ Redis connection failed: {e}")
        else:
            logger.warning("⚠ Redis not configured")
        
        # Test Twilio connection
        if self.service.twilio_client:
            try:
                # Test by getting account info
                account = self.service.twilio_client.api.accounts.get()
                logger.info(f"✓ Twilio connection successful (Account: {account.friendly_name})")
            except Exception as e:
                logger.error(f"✗ Twilio connection failed: {e}")
        else:
            logger.warning("⚠ Twilio not configured")
        
        # Test API connectivity
        test_ticker = "AAPL"
        try:
            sentiment = await self.service.fetch_sentiment_data(test_ticker)
            if sentiment:
                logger.info(f"✓ API connection successful (fetched {test_ticker} sentiment)")
            else:
                logger.warning("⚠ API connection failed or returned no data")
        except Exception as e:
            logger.error(f"✗ API connection failed: {e}")
        
        logger.info("Service test completed")
        return True


def main():
    """Main entry point for cron scheduler."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Sentiment Monitoring Cron Scheduler")
    parser.add_argument("--mode", choices=["schedule", "crontab", "test", "single"], 
                       default="schedule", help="Scheduler mode")
    parser.add_argument("--interval", type=int, default=60, 
                       help="Check interval in minutes (default: 60)")
    parser.add_argument("--config", default="config.yml", 
                       help="Configuration file path")
    
    args = parser.parse_args()
    
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    scheduler = CronScheduler(args.config)
    
    if args.mode == "schedule":
        # Use Python-based scheduler
        scheduler.start_python_scheduler(args.interval)
    
    elif args.mode == "crontab":
        # Generate crontab entry
        scheduler.install_crontab(args.interval)
    
    elif args.mode == "test":
        # Test service
        asyncio.run(scheduler.test_service())
    
    elif args.mode == "single":
        # Run single check
        asyncio.run(scheduler.run_single_check())


if __name__ == "__main__":
    main() 