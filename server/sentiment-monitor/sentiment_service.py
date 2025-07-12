#!/usr/bin/env python3
"""
Sentiment Monitoring Service

This service monitors sentiment data from the hedge fund API and sends alerts
when significant sentiment changes are detected.
"""

import os
import sys
import time
import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

import requests
import yaml
from loguru import logger
from twilio.rest import Client as TwilioClient
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import redis
from pydantic import BaseModel


# Configuration Models
@dataclass
class AlertConfig:
    cooldown_minutes: int
    sentiment_threshold_positive: float
    sentiment_threshold_negative: float


@dataclass
class ServiceConfig:
    name: str
    log_level: str
    environment: str
    check_interval_minutes: int


class SentimentData(BaseModel):
    ticker: str
    sentiment_score: float
    sentiment_label: str
    confidence: float
    timestamp: datetime
    source: str = "hedge_fund_api"


# Database Models
Base = declarative_base()


class SentimentRecord(Base):
    __tablename__ = "sentiment_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), nullable=False, index=True)
    sentiment_score = Column(Float, nullable=False)
    sentiment_label = Column(String(20), nullable=False)
    confidence = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    source = Column(String(50), nullable=False)
    raw_data = Column(Text)  # JSON string of raw API response


class AlertRecord(Base):
    __tablename__ = "alert_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), nullable=False, index=True)
    alert_type = Column(String(20), nullable=False)  # 'positive', 'negative'
    sentiment_score = Column(Float, nullable=False)
    message = Column(Text, nullable=False)
    phone_numbers = Column(Text)  # JSON array of phone numbers
    sent_at = Column(DateTime, nullable=False)
    success = Column(String(10), nullable=False)  # 'success', 'failed'
    error_message = Column(Text)


class SentimentMonitorService:
    """Main sentiment monitoring service."""
    
    def __init__(self, config_path: str = "config.yml"):
        self.config = self._load_config(config_path)
        self._setup_logging()
        self._setup_database()
        self._setup_redis()
        self._setup_twilio()
        logger.info("Sentiment monitoring service initialized")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file {config_path} not found")
            sys.exit(1)
        except yaml.YAMLError as e:
            logger.error(f"Error parsing configuration file: {e}")
            sys.exit(1)
    
    def _setup_logging(self):
        """Configure logging."""
        log_config = self.config.get('logging', {})
        log_level = self.config.get('service', {}).get('log_level', 'INFO')
        
        # Remove default logger
        logger.remove()
        
        # Add console logger
        logger.add(
            sys.stderr,
            level=log_level,
            format=log_config.get('format', "{time} | {level} | {message}")
        )
        
        # Add file logger
        logger.add(
            "logs/sentiment_monitor_{time:YYYY-MM-DD}.log",
            level=log_level,
            format=log_config.get('format', "{time} | {level} | {message}"),
            rotation=log_config.get('rotation', "1 day"),
            retention=log_config.get('retention', "30 days")
        )
    
    def _setup_database(self):
        """Setup database connection and create tables."""
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.warning("DATABASE_URL not set, using SQLite")
            database_url = "sqlite:///sentiment_monitor.db"
        
        self.engine = create_engine(database_url, pool_pre_ping=True)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        logger.info("Database connection established")
    
    def _setup_redis(self):
        """Setup Redis connection for caching and cooldowns."""
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        try:
            self.redis_client = redis.from_url(redis_url)
            self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Continuing without Redis.")
            self.redis_client = None
    
    def _setup_twilio(self):
        """Setup Twilio client for SMS alerts."""
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        
        if account_sid and auth_token:
            self.twilio_client = TwilioClient(account_sid, auth_token)
            self.twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')
            self.alert_phones = os.getenv('ALERT_PHONE_NUMBERS', '').split(',')
            self.alert_phones = [phone.strip() for phone in self.alert_phones if phone.strip()]
            logger.info(f"Twilio client initialized for {len(self.alert_phones)} recipients")
        else:
            logger.warning("Twilio credentials not found. SMS alerts disabled.")
            self.twilio_client = None
    
    def get_db_session(self) -> Session:
        """Get database session."""
        return self.SessionLocal()
    
    async def fetch_sentiment_data(self, ticker: str) -> Optional[SentimentData]:
        """Fetch sentiment data for a ticker from the hedge fund API."""
        api_config = self.config.get('api', {})
        url = f"{api_config.get('sentiment_url')}/{ticker}"
        timeout = api_config.get('timeout', 30)
        
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse the API response - adjust based on actual API format
            return SentimentData(
                ticker=ticker,
                sentiment_score=data.get('sentiment_score', 0.0),
                sentiment_label=data.get('sentiment_label', 'neutral'),
                confidence=data.get('confidence', 0.0),
                timestamp=datetime.now(),
                source='hedge_fund_api'
            )
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch sentiment for {ticker}: {e}")
            return None
        except (KeyError, ValueError) as e:
            logger.error(f"Failed to parse sentiment data for {ticker}: {e}")
            return None
    
    def store_sentiment_data(self, sentiment: SentimentData, raw_data: Dict[str, Any]):
        """Store sentiment data in database."""
        with self.get_db_session() as db:
            try:
                record = SentimentRecord(
                    ticker=sentiment.ticker,
                    sentiment_score=sentiment.sentiment_score,
                    sentiment_label=sentiment.sentiment_label,
                    confidence=sentiment.confidence,
                    timestamp=sentiment.timestamp,
                    source=sentiment.source,
                    raw_data=json.dumps(raw_data)
                )
                db.add(record)
                db.commit()
                logger.debug(f"Stored sentiment data for {sentiment.ticker}")
            except Exception as e:
                logger.error(f"Failed to store sentiment data for {sentiment.ticker}: {e}")
                db.rollback()
    
    def check_alert_cooldown(self, ticker: str, alert_type: str) -> bool:
        """Check if we're in cooldown period for this ticker/alert type."""
        if not self.redis_client:
            return False
        
        cooldown_key = f"alert_cooldown:{ticker}:{alert_type}"
        cooldown_minutes = self.config.get('alerts', {}).get('cooldown_minutes', 120)
        
        try:
            return self.redis_client.exists(cooldown_key)
        except Exception as e:
            logger.error(f"Redis cooldown check failed: {e}")
            return False
    
    def set_alert_cooldown(self, ticker: str, alert_type: str):
        """Set alert cooldown for ticker/alert type."""
        if not self.redis_client:
            return
        
        cooldown_key = f"alert_cooldown:{ticker}:{alert_type}"
        cooldown_minutes = self.config.get('alerts', {}).get('cooldown_minutes', 120)
        
        try:
            self.redis_client.setex(cooldown_key, cooldown_minutes * 60, "1")
        except Exception as e:
            logger.error(f"Failed to set alert cooldown: {e}")
    
    async def send_sms_alert(self, message: str, phone_numbers: List[str]) -> bool:
        """Send SMS alert via Twilio."""
        if not self.twilio_client or not self.twilio_phone:
            logger.warning("Twilio not configured, skipping SMS alert")
            return False
        
        success_count = 0
        for phone_number in phone_numbers:
            try:
                message_obj = self.twilio_client.messages.create(
                    body=message,
                    from_=self.twilio_phone,
                    to=phone_number
                )
                logger.info(f"SMS sent to {phone_number}: {message_obj.sid}")
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to send SMS to {phone_number}: {e}")
        
        return success_count > 0
    
    def should_alert(self, sentiment: SentimentData) -> Optional[str]:
        """Check if sentiment data should trigger an alert."""
        alert_config = self.config.get('alerts', {})
        positive_threshold = alert_config.get('sentiment_threshold_positive', 0.7)
        negative_threshold = alert_config.get('sentiment_threshold_negative', -0.7)
        
        if sentiment.sentiment_score >= positive_threshold:
            return 'positive'
        elif sentiment.sentiment_score <= negative_threshold:
            return 'negative'
        
        return None
    
    async def process_sentiment_alert(self, sentiment: SentimentData):
        """Process and send sentiment alert if needed."""
        alert_type = self.should_alert(sentiment)
        if not alert_type:
            return
        
        # Check cooldown
        if self.check_alert_cooldown(sentiment.ticker, alert_type):
            logger.debug(f"Alert for {sentiment.ticker} {alert_type} sentiment is in cooldown")
            return
        
        # Create alert message
        if alert_type == 'positive':
            message = f"🚀 STRONG POSITIVE sentiment detected for ${sentiment.ticker}!\n"
        else:
            message = f"⚠️ STRONG NEGATIVE sentiment detected for ${sentiment.ticker}!\n"
        
        message += f"Score: {sentiment.sentiment_score:.3f}\n"
        message += f"Confidence: {sentiment.confidence:.1%}\n"
        message += f"Time: {sentiment.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Send alert
        success = await self.send_sms_alert(message, self.alert_phones)
        
        # Record alert in database
        with self.get_db_session() as db:
            try:
                alert_record = AlertRecord(
                    ticker=sentiment.ticker,
                    alert_type=alert_type,
                    sentiment_score=sentiment.sentiment_score,
                    message=message,
                    phone_numbers=json.dumps(self.alert_phones),
                    sent_at=datetime.now(),
                    success='success' if success else 'failed',
                    error_message=None if success else 'SMS sending failed'
                )
                db.add(alert_record)
                db.commit()
                
                if success:
                    # Set cooldown
                    self.set_alert_cooldown(sentiment.ticker, alert_type)
                    logger.info(f"Alert sent for {sentiment.ticker} {alert_type} sentiment")
                else:
                    logger.error(f"Failed to send alert for {sentiment.ticker}")
                    
            except Exception as e:
                logger.error(f"Failed to record alert: {e}")
                db.rollback()
    
    async def monitor_ticker(self, ticker: str):
        """Monitor sentiment for a single ticker."""
        logger.debug(f"Monitoring sentiment for {ticker}")
        
        # Fetch sentiment data
        sentiment = await self.fetch_sentiment_data(ticker)
        if not sentiment:
            return
        
        # Store in database
        self.store_sentiment_data(sentiment, {"ticker": ticker})
        
        # Check for alerts
        await self.process_sentiment_alert(sentiment)
    
    async def run_monitoring_cycle(self):
        """Run a complete monitoring cycle for all tickers."""
        tickers = self.config.get('monitoring', {}).get('tickers', [])
        logger.info(f"Starting monitoring cycle for {len(tickers)} tickers")
        
        # Monitor all tickers concurrently
        tasks = [self.monitor_ticker(ticker) for ticker in tickers]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info("Monitoring cycle completed")
    
    async def run_service(self):
        """Main service loop."""
        check_interval = self.config.get('service', {}).get('check_interval_minutes', 60)
        logger.info(f"Starting sentiment monitoring service (checking every {check_interval} minutes)")
        
        while True:
            try:
                await self.run_monitoring_cycle()
                
                # Wait for next cycle
                logger.info(f"Waiting {check_interval} minutes until next check...")
                await asyncio.sleep(check_interval * 60)
                
            except KeyboardInterrupt:
                logger.info("Service interrupted by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error in service loop: {e}")
                # Wait a bit before retrying
                await asyncio.sleep(60)
    
    def get_recent_alerts(self, hours: int = 24) -> List[AlertRecord]:
        """Get recent alerts from database."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self.get_db_session() as db:
            return db.query(AlertRecord).filter(
                AlertRecord.sent_at >= cutoff_time
            ).order_by(AlertRecord.sent_at.desc()).all()
    
    def get_sentiment_history(self, ticker: str, hours: int = 24) -> List[SentimentRecord]:
        """Get sentiment history for a ticker."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self.get_db_session() as db:
            return db.query(SentimentRecord).filter(
                SentimentRecord.ticker == ticker,
                SentimentRecord.timestamp >= cutoff_time
            ).order_by(SentimentRecord.timestamp.desc()).all()


if __name__ == "__main__":
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    # Initialize and run service
    service = SentimentMonitorService()
    asyncio.run(service.run_service()) 