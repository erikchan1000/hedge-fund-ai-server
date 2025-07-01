from flask import Flask
from .routes.analysis import analysis_bp
from .routes.portfolio import portfolio_bp
from .routes.health import health_bp
from .routes.docs import docs_bp
from .routes.search_tickers import search_tickers_bp

def init_app(app: Flask) -> None:
    """Initialize the API with the Flask app using new MCS structure."""
    app.register_blueprint(analysis_bp)
    app.register_blueprint(portfolio_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(docs_bp)
    app.register_blueprint(search_tickers_bp)