"""Core exception classes for the application."""

class BaseApplicationError(Exception):
    """Base exception class for all application errors."""
    
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__

class ValidationError(BaseApplicationError):
    """Raised when input validation fails."""
    pass

class BusinessLogicError(BaseApplicationError):
    """Raised when business logic validation fails."""
    pass

class ExternalServiceError(BaseApplicationError):
    """Raised when external service calls fail."""
    
    def __init__(self, message: str, service_name: str = None, status_code: int = None):
        super().__init__(message)
        self.service_name = service_name
        self.status_code = status_code

class ConfigurationError(BaseApplicationError):
    """Raised when configuration is invalid or missing."""
    pass

class DataNotFoundError(BaseApplicationError):
    """Raised when requested data is not found."""
    pass

class AuthenticationError(BaseApplicationError):
    """Raised when authentication fails."""
    pass

class AuthorizationError(BaseApplicationError):
    """Raised when authorization fails."""
    pass

class RateLimitError(BaseApplicationError):
    """Raised when rate limits are exceeded."""
    
    def __init__(self, message: str, retry_after: int = None):
        super().__init__(message)
        self.retry_after = retry_after 