"""Utilities for streaming progress updates in LangGraph agents."""

import functools
from typing import Callable, Any, Optional
from datetime import datetime
from langgraph.config import get_stream_writer
from src.utils.cancellation import CancellationToken, CancellationException


def with_streaming_progress(agent_name: str = None):
    """
    Decorator that automatically adds stream writer progress updates to agent functions.
    
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
            # Get stream writer for progress updates
            writer = get_stream_writer()
            name = agent_name or func.__name__
            
            # Extract tickers from state
            tickers = state.get("data", {}).get("tickers", [])
            
            # Check for cancellation token in state
            cancellation_token = state.get("cancellation_token")
            
            # Check for cancellation before starting
            if cancellation_token:
                cancellation_token.check_cancelled()
            
            # Emit start progress
            if writer:
                writer({
                    "type": "progress",
                    "stage": "analysis",
                    "message": f"Starting {name} analysis...",
                    "current_analyst": name,
                    "timestamp": datetime.now().isoformat()
                })
            
            try:
                # Execute the original function
                result = func(state, *args, **kwargs)
                
                # Check for cancellation after execution
                if cancellation_token:
                    cancellation_token.check_cancelled()
                
                # Emit completion progress
                if writer:
                    writer({
                        "type": "progress",
                        "stage": "analysis",
                        "message": f"Completed {name} analysis",
                        "current_analyst": name,
                        "timestamp": datetime.now().isoformat()
                    })
                
                return result
                
            except CancellationException:
                # Emit cancellation progress
                if writer:
                    writer({
                        "type": "progress",
                        "stage": "cancelled",
                        "message": f"Cancelled {name} analysis",
                        "current_analyst": name,
                        "timestamp": datetime.now().isoformat()
                    })
                raise
            except Exception as e:
                # Emit error progress
                if writer:
                    writer({
                        "type": "progress",
                        "stage": "error",
                        "message": f"Error in {name} analysis: {str(e)}",
                        "current_analyst": name,
                        "timestamp": datetime.now().isoformat()
                    })
                raise
        
        return wrapper
    return decorator


def emit_progress(message: str, stage: str = "analysis", analyst_name: str = None, cancellation_token: Optional[CancellationToken] = None):
    """
    Utility function to emit a progress update using get_stream_writer.
    
    Args:
        message: The progress message
        stage: The current stage (default: "analysis")
        analyst_name: Optional analyst name
        cancellation_token: Optional cancellation token to check
    """
    # Check for cancellation before emitting progress
    if cancellation_token:
        cancellation_token.check_cancelled()
    
    writer = get_stream_writer()
    if writer:
        writer({
            "type": "progress",
            "stage": stage,
            "message": message,
            "current_analyst": analyst_name,
            "timestamp": datetime.now().isoformat()
        })


def emit_ticker_progress(ticker: str, message: str, analyst_name: str = None, cancellation_token: Optional[CancellationToken] = None):
    """
    Utility function to emit a ticker-specific progress update.
    
    Args:
        ticker: The ticker symbol
        message: The progress message
        analyst_name: Optional analyst name
        cancellation_token: Optional cancellation token to check
    """
    emit_progress(f"{ticker}: {message}", "analysis", analyst_name, cancellation_token)


def with_cancellation_check(func: Callable) -> Callable:
    """
    Decorator that adds cancellation checking to any function.
    
    Usage:
        @with_cancellation_check
        def my_function(state: AgentState):
            # Your function logic here
            pass
    """
    @functools.wraps(func)
    def wrapper(state: Any, *args, **kwargs):
        # Check for cancellation token in state
        cancellation_token = state.get("cancellation_token")
        
        # Check for cancellation before execution
        if cancellation_token:
            cancellation_token.check_cancelled()
        
        try:
            result = func(state, *args, **kwargs)
            
            # Check for cancellation after execution
            if cancellation_token:
                cancellation_token.check_cancelled()
            
            return result
            
        except CancellationException:
            # Re-raise cancellation exceptions
            raise
        except Exception as e:
            # For other exceptions, still check if we were cancelled
            if cancellation_token and cancellation_token.is_cancelled:
                raise CancellationException("Operation was cancelled")
            raise
    
    return wrapper 