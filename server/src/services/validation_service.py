from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging

from src.models.dto.requests import AnalysisRequestDTO
from src.core.exceptions import ValidationError
from src.utils.analysts import ANALYST_CONFIG

logger = logging.getLogger(__name__)

class ValidationService:
    """Service for handling business validation logic."""
    
    def validate_analysis_request(self, request_dto: AnalysisRequestDTO) -> None:
        """Validate analysis request business rules."""
        
        # Validate tickers
        if not request_dto.tickers:
            raise ValidationError("At least one ticker must be provided")
        
        if len(request_dto.tickers) > 50:  # Reasonable limit
            raise ValidationError("Too many tickers provided (max 50)")
        
        # Validate tickers format
        for ticker in request_dto.tickers:
            if not self._is_valid_ticker_format(ticker):
                raise ValidationError(f"Invalid ticker format: {ticker}")
        
        # Validate dates
        if request_dto.end_date and not self.validate_date(request_dto.end_date):
            raise ValidationError("Invalid end_date format. Use YYYY-MM-DD")
        
        if request_dto.start_date and not self.validate_date(request_dto.start_date):
            raise ValidationError("Invalid start_date format. Use YYYY-MM-DD")
        
        # Validate date range
        if request_dto.start_date and request_dto.end_date:
            start_date = datetime.strptime(request_dto.start_date, '%Y-%m-%d')
            end_date = datetime.strptime(request_dto.end_date, '%Y-%m-%d')
            
            if start_date >= end_date:
                raise ValidationError("start_date must be before end_date")
            
            # Check if date range is too large (e.g., more than 5 years)
            if (end_date - start_date).days > 1825:  # 5 years
                raise ValidationError("Date range too large (max 5 years)")
        
        # Validate financial values
        if request_dto.initial_cash <= 0:
            raise ValidationError("initial_cash must be positive")
        
        if request_dto.initial_cash > 1000000000:  # 1 billion limit
            raise ValidationError("initial_cash too large (max 1 billion)")
        
        if request_dto.margin_requirement < 0:
            raise ValidationError("margin_requirement cannot be negative")
        
        # Validate model parameters
        if not request_dto.model_name:
            raise ValidationError("model_name is required")
        
        if not request_dto.model_provider:
            raise ValidationError("model_provider is required")
        
        # Validate analysts
        if request_dto.selected_analysts:
            valid_analysts = self._get_valid_analysts()
            for analyst in request_dto.selected_analysts:
                if analyst not in valid_analysts:
                    raise ValidationError(f"Invalid analyst: {analyst}")
    
    def validate_date(self, date_str: str) -> bool:
        """Validate if a string is in YYYY-MM-DD format."""
        try:
            parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
            
            # Check if date is not too far in the future
            max_future_date = datetime.now() + timedelta(days=30)
            if parsed_date > max_future_date:
                return False
            
            # Check if date is not too far in the past
            min_past_date = datetime.now() - timedelta(days=365 * 20)  # 20 years
            if parsed_date < min_past_date:
                return False
            
            return True
        except ValueError:
            return False
    
    def _is_valid_ticker_format(self, ticker: str) -> bool:
        """Validate ticker symbol format."""
        if not ticker:
            return False
        
        # Basic validation: 1-10 characters, alphanumeric, may contain dots/hyphens
        if len(ticker) < 1 or len(ticker) > 10:
            return False
        
        # Allow letters, numbers, dots, and hyphens
        allowed_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-")
        return all(c in allowed_chars for c in ticker.upper())
    
    def _get_valid_analysts(self) -> List[str]:
        """Get list of valid analyst names from ANALYST_CONFIG."""
        return list(ANALYST_CONFIG.keys()) 