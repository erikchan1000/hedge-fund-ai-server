"""Utilities for streaming progress updates in LangGraph agents."""

import functools
from typing import Callable, Any
from datetime import datetime
from langgraph.graph import StreamWriter


def with_streaming_progress(agent_name: str = None):
    """
    Decorator that automatically adds StreamWriter progress updates to agent functions.
    
    Args:
        agent_name: Optional name for the agent. If not provided, will use the function name.
    
    Usage:
        @with_streaming_progress("warren_buffett")
        def warren_buffett_agent(state: AgentState):
            # Your agent logic here
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(state: Any, *args, **kwargs):
            # Get StreamWriter for progress updates
            writer = StreamWriter.get_current()
            name = agent_name or func.__name__
            
            # Extract tickers from state
            tickers = state.get("data", {}).get("tickers", [])
            
            # Emit start progress
            if writer:
                writer.write({
                    "type": "progress",
                    "stage": "analysis",
                    "message": f"Starting {name} analysis...",
                    "current_analyst": name,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Execute the original function
            result = func(state, *args, **kwargs)
            
            # Emit completion progress
            if writer:
                writer.write({
                    "type": "progress",
                    "stage": "analysis",
                    "message": f"Completed {name} analysis",
                    "current_analyst": name,
                    "timestamp": datetime.now().isoformat()
                })
            
            return result
        
        return wrapper
    return decorator


def emit_progress(message: str, stage: str = "analysis", analyst_name: str = None):
    """
    Utility function to emit a progress update using StreamWriter.
    
    Args:
        message: The progress message
        stage: The current stage (default: "analysis")
        analyst_name: Optional analyst name
    """
    writer = StreamWriter.get_current()
    if writer:
        writer.write({
            "type": "progress",
            "stage": stage,
            "message": message,
            "current_analyst": analyst_name,
            "timestamp": datetime.now().isoformat()
        })


def emit_ticker_progress(ticker: str, message: str, analyst_name: str = None):
    """
    Utility function to emit a ticker-specific progress update.
    
    Args:
        ticker: The ticker symbol
        message: The progress message
        analyst_name: Optional analyst name
    """
    emit_progress(f"{ticker}: {message}", "analysis", analyst_name) 