"""API routes package for the hedge fund system."""

from .analysis import analysis_bp
from .portfolio import portfolio_bp
from .health import health_bp
from .docs import docs_bp

__all__ = ['analysis_bp', 'portfolio_bp', 'health_bp', 'docs_bp'] 