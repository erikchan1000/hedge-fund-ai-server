"""Request cancellation management utilities."""

import asyncio
import threading
import time
import logging
from typing import Dict, Optional, Set, Callable, Any
from uuid import uuid4
from contextlib import contextmanager
from dataclasses import dataclass
from concurrent.futures import Future, ThreadPoolExecutor

logger = logging.getLogger(__name__)

@dataclass
class CancellationToken:
    """Token for managing request cancellation."""
    request_id: str
    is_cancelled: bool = False
    cancel_callbacks: Set[Callable] = None
    
    def __post_init__(self):
        if self.cancel_callbacks is None:
            self.cancel_callbacks = set()
    
    def cancel(self):
        """Cancel the request and trigger all callbacks."""
        if not self.is_cancelled:
            self.is_cancelled = True
            logger.info(f"Cancelling request {self.request_id}")
            
            # Execute all cancel callbacks
            for callback in self.cancel_callbacks:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Error executing cancel callback: {e}")
            
            self.cancel_callbacks.clear()
    
    def add_cancel_callback(self, callback: Callable):
        """Add a callback to be executed when the request is cancelled."""
        if self.is_cancelled:
            # If already cancelled, execute immediately
            try:
                callback()
            except Exception as e:
                logger.error(f"Error executing immediate cancel callback: {e}")
        else:
            self.cancel_callbacks.add(callback)
    
    def check_cancelled(self):
        """Check if the request has been cancelled and raise an exception if so."""
        if self.is_cancelled:
            raise CancellationException(f"Request {self.request_id} was cancelled")


class CancellationException(Exception):
    """Exception raised when a request is cancelled."""
    pass


class CancellationManager:
    """Manages request cancellation across the application."""
    
    def __init__(self):
        self._active_requests: Dict[str, CancellationToken] = {}
        self._lock = threading.RLock()
        self._cleanup_interval = 300  # 5 minutes
        self._max_request_age = 3600  # 1 hour
        self._request_timestamps: Dict[str, float] = {}
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="cancellation-")
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()
    
    def create_cancellation_token(self, request_id: Optional[str] = None) -> CancellationToken:
        """Create a new cancellation token for a request."""
        if request_id is None:
            request_id = str(uuid4())
        
        token = CancellationToken(request_id=request_id)
        
        with self._lock:
            self._active_requests[request_id] = token
            self._request_timestamps[request_id] = time.time()
        
        logger.debug(f"Created cancellation token for request {request_id}")
        return token
    
    def cancel_request(self, request_id: str) -> bool:
        """Cancel a specific request by ID."""
        with self._lock:
            token = self._active_requests.get(request_id)
            if token:
                token.cancel()
                self._cleanup_request(request_id)
                return True
            return False
    
    def cancel_all_requests(self):
        """Cancel all active requests."""
        with self._lock:
            active_requests = list(self._active_requests.items())
        
        logger.info(f"Cancelling {len(active_requests)} active requests")
        
        for request_id, token in active_requests:
            try:
                token.cancel()
            except Exception as e:
                logger.error(f"Error cancelling request {request_id}: {e}")
        
        with self._lock:
            self._active_requests.clear()
            self._request_timestamps.clear()
    
    def get_active_request_count(self) -> int:
        """Get the number of active requests."""
        with self._lock:
            return len(self._active_requests)
    
    def get_active_request_ids(self) -> Set[str]:
        """Get the IDs of all active requests."""
        with self._lock:
            return set(self._active_requests.keys())
    
    def _cleanup_request(self, request_id: str):
        """Clean up a finished request."""
        with self._lock:
            self._active_requests.pop(request_id, None)
            self._request_timestamps.pop(request_id, None)
    
    def _cleanup_loop(self):
        """Background thread to clean up old requests."""
        while True:
            try:
                time.sleep(self._cleanup_interval)
                self._cleanup_old_requests()
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
    def _cleanup_old_requests(self):
        """Clean up requests that are too old."""
        current_time = time.time()
        old_requests = []
        
        with self._lock:
            for request_id, timestamp in self._request_timestamps.items():
                if current_time - timestamp > self._max_request_age:
                    old_requests.append(request_id)
        
        for request_id in old_requests:
            logger.warning(f"Cleaning up old request {request_id}")
            self.cancel_request(request_id)
    
    @contextmanager
    def cancellable_request(self, request_id: Optional[str] = None):
        """Context manager for cancellable requests."""
        token = self.create_cancellation_token(request_id)
        try:
            yield token
        except CancellationException:
            logger.info(f"Request {token.request_id} was cancelled during execution")
            raise
        except Exception as e:
            logger.error(f"Error in cancellable request {token.request_id}: {e}")
            raise
        finally:
            self._cleanup_request(token.request_id)
    
    def shutdown(self):
        """Shutdown the cancellation manager."""
        logger.info("Shutting down cancellation manager")
        self.cancel_all_requests()
        self._executor.shutdown(wait=True)


# Global cancellation manager instance
_cancellation_manager = CancellationManager()

def get_cancellation_manager() -> CancellationManager:
    """Get the global cancellation manager instance."""
    return _cancellation_manager

def create_cancellation_token(request_id: Optional[str] = None) -> CancellationToken:
    """Create a new cancellation token."""
    return _cancellation_manager.create_cancellation_token(request_id)

def cancel_request(request_id: str) -> bool:
    """Cancel a specific request."""
    return _cancellation_manager.cancel_request(request_id)

def cancel_all_requests():
    """Cancel all active requests."""
    _cancellation_manager.cancel_all_requests()

@contextmanager
def cancellable_request(request_id: Optional[str] = None):
    """Context manager for cancellable requests."""
    with _cancellation_manager.cancellable_request(request_id) as token:
        yield token 