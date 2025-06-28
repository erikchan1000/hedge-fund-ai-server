from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class AnalysisProgressDTO:
    """Data Transfer Object for analysis progress updates."""
    
    type: str  # "progress", "result", "error"
    stage: str
    message: str
    progress: int
    timestamp: Optional[str] = None
    analysts: Optional[List[str]] = None
    tickers: Optional[List[str]] = None
    current_analyst: Optional[str] = None
    analyst_progress: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert DTO to dictionary."""
        result = {
            'type': self.type,
            'stage': self.stage,
            'message': self.message,
            'progress': self.progress,
            'timestamp': self.timestamp
        }
        
        # Add optional fields if present
        if self.analysts is not None:
            result['analysts'] = self.analysts
        if self.tickers is not None:
            result['tickers'] = self.tickers
        if self.current_analyst is not None:
            result['current_analyst'] = self.current_analyst
        if self.analyst_progress is not None:
            result['analyst_progress'] = self.analyst_progress
        
        return result

@dataclass
class AnalysisResultDTO:
    """Data Transfer Object for analysis results."""
    
    type: str = "result"
    data: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert DTO to dictionary."""
        return {
            'type': self.type,
            'data': self.data,
            'timestamp': self.timestamp
        }

@dataclass
class ErrorResponseDTO:
    """Data Transfer Object for error responses."""
    
    type: str = "error"
    message: str = ""
    stage: Optional[str] = None
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert DTO to dictionary."""
        result = {
            'type': self.type,
            'message': self.message,
            'timestamp': self.timestamp
        }
        
        if self.stage is not None:
            result['stage'] = self.stage
        
        return result 