#!/usr/bin/env python3
"""
Web API for Sentiment Monitoring Service

Provides a REST API for monitoring service status, viewing recent alerts,
and manually triggering sentiment checks.
"""

import os
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from loguru import logger

from sentiment_service import SentimentMonitorService, SentimentRecord, AlertRecord


# API Models
class ServiceStatus(BaseModel):
    status: str
    last_check: Optional[datetime] = None
    next_check: Optional[datetime] = None
    uptime: str
    database_connected: bool
    redis_connected: bool
    twilio_configured: bool


class AlertSummary(BaseModel):
    id: int
    ticker: str
    alert_type: str
    sentiment_score: float
    sent_at: datetime
    success: str
    phone_count: int


class SentimentSummary(BaseModel):
    ticker: str
    sentiment_score: float
    sentiment_label: str
    confidence: float
    timestamp: datetime


class TriggerResponse(BaseModel):
    message: str
    task_id: str


# Initialize FastAPI app
app = FastAPI(
    title="Sentiment Monitor API",
    description="REST API for monitoring sentiment analysis and alerts",
    version="1.0.0"
)

# Global service instance
service = None
start_time = datetime.now()
background_tasks = {}


@app.on_event("startup")
async def startup_event():
    """Initialize the sentiment service on startup."""
    global service
    try:
        service = SentimentMonitorService()
        logger.info("Sentiment monitoring service initialized for web API")
    except Exception as e:
        logger.error(f"Failed to initialize sentiment service: {e}")
        raise


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now()}


@app.get("/status", response_model=ServiceStatus)
async def get_service_status():
    """Get current service status."""
    if not service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    # Check database connection
    database_connected = True
    try:
        with service.get_db_session() as db:
            db.execute("SELECT 1")
    except Exception:
        database_connected = False
    
    # Check Redis connection
    redis_connected = False
    if service.redis_client:
        try:
            service.redis_client.ping()
            redis_connected = True
        except Exception:
            pass
    
    # Check Twilio configuration
    twilio_configured = service.twilio_client is not None
    
    # Calculate uptime
    uptime_delta = datetime.now() - start_time
    uptime_str = str(uptime_delta).split('.')[0]  # Remove microseconds
    
    return ServiceStatus(
        status="running",
        last_check=None,  # Would need to track this
        next_check=None,  # Would need to track this
        uptime=uptime_str,
        database_connected=database_connected,
        redis_connected=redis_connected,
        twilio_configured=twilio_configured
    )


@app.get("/alerts/recent", response_model=List[AlertSummary])
async def get_recent_alerts(hours: int = 24):
    """Get recent alerts from the last N hours."""
    if not service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        alerts = service.get_recent_alerts(hours)
        return [
            AlertSummary(
                id=alert.id,
                ticker=alert.ticker,
                alert_type=alert.alert_type,
                sentiment_score=alert.sentiment_score,
                sent_at=alert.sent_at,
                success=alert.success,
                phone_count=len(eval(alert.phone_numbers)) if alert.phone_numbers else 0
            )
            for alert in alerts
        ]
    except Exception as e:
        logger.error(f"Error fetching recent alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch alerts")


@app.get("/sentiment/{ticker}", response_model=List[SentimentSummary])
async def get_sentiment_history(ticker: str, hours: int = 24):
    """Get sentiment history for a specific ticker."""
    if not service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        history = service.get_sentiment_history(ticker.upper(), hours)
        return [
            SentimentSummary(
                ticker=record.ticker,
                sentiment_score=record.sentiment_score,
                sentiment_label=record.sentiment_label,
                confidence=record.confidence,
                timestamp=record.timestamp
            )
            for record in history
        ]
    except Exception as e:
        logger.error(f"Error fetching sentiment history for {ticker}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch sentiment history")


@app.get("/sentiment/all", response_model=Dict[str, List[SentimentSummary]])
async def get_all_sentiment_history(hours: int = 24):
    """Get sentiment history for all monitored tickers."""
    if not service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        tickers = service.config.get('monitoring', {}).get('tickers', [])
        result = {}
        
        for ticker in tickers:
            history = service.get_sentiment_history(ticker, hours)
            result[ticker] = [
                SentimentSummary(
                    ticker=record.ticker,
                    sentiment_score=record.sentiment_score,
                    sentiment_label=record.sentiment_label,
                    confidence=record.confidence,
                    timestamp=record.timestamp
                )
                for record in history
            ]
        
        return result
    except Exception as e:
        logger.error(f"Error fetching all sentiment history: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch sentiment history")


@app.post("/trigger/check", response_model=TriggerResponse)
async def trigger_manual_check(background_tasks: BackgroundTasks):
    """Manually trigger a sentiment monitoring cycle."""
    if not service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    task_id = f"manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    async def run_check():
        try:
            logger.info(f"Starting manual sentiment check (task: {task_id})")
            await service.run_monitoring_cycle()
            logger.info(f"Manual sentiment check completed (task: {task_id})")
            background_tasks[task_id] = "completed"
        except Exception as e:
            logger.error(f"Manual sentiment check failed (task: {task_id}): {e}")
            background_tasks[task_id] = f"failed: {e}"
    
    # Run the check in the background
    background_tasks.add_task(run_check)
    background_tasks[task_id] = "running"
    
    return TriggerResponse(
        message="Manual sentiment check triggered",
        task_id=task_id
    )


@app.post("/trigger/check/{ticker}", response_model=TriggerResponse)
async def trigger_ticker_check(ticker: str, background_tasks: BackgroundTasks):
    """Manually trigger sentiment check for a specific ticker."""
    if not service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    ticker = ticker.upper()
    task_id = f"manual_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    async def run_ticker_check():
        try:
            logger.info(f"Starting manual sentiment check for {ticker} (task: {task_id})")
            await service.monitor_ticker(ticker)
            logger.info(f"Manual sentiment check for {ticker} completed (task: {task_id})")
            background_tasks[task_id] = "completed"
        except Exception as e:
            logger.error(f"Manual sentiment check for {ticker} failed (task: {task_id}): {e}")
            background_tasks[task_id] = f"failed: {e}"
    
    # Run the check in the background
    background_tasks.add_task(run_ticker_check)
    background_tasks[task_id] = "running"
    
    return TriggerResponse(
        message=f"Manual sentiment check for {ticker} triggered",
        task_id=task_id
    )


@app.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """Get status of a background task."""
    if task_id not in background_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "task_id": task_id,
        "status": background_tasks[task_id]
    }


@app.get("/config")
async def get_configuration():
    """Get current service configuration (excluding sensitive data)."""
    if not service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    # Return config without sensitive information
    safe_config = {
        "service": service.config.get('service', {}),
        "monitoring": service.config.get('monitoring', {}),
        "alerts": {
            k: v for k, v in service.config.get('alerts', {}).items()
            if k not in ['twilio_account_sid', 'twilio_auth_token']
        }
    }
    
    return safe_config


@app.get("/logs/recent")
async def get_recent_logs(lines: int = 100):
    """Get recent log entries."""
    try:
        log_file = "logs/sentiment_monitor_" + datetime.now().strftime("%Y-%m-%d") + ".log"
        
        if not os.path.exists(log_file):
            return {"logs": [], "message": "No log file found for today"}
        
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        return {
            "logs": [line.strip() for line in recent_lines],
            "total_lines": len(all_lines),
            "showing_lines": len(recent_lines)
        }
    except Exception as e:
        logger.error(f"Error reading log file: {e}")
        raise HTTPException(status_code=500, detail="Failed to read log file")


if __name__ == "__main__":
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    # Run the web API
    uvicorn.run(
        "web_api:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False
    ) 