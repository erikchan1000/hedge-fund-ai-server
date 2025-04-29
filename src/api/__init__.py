from flask import Flask
from .routes import api_bp

def init_app(app: Flask) -> None:
    """Initialize the API with the Flask app."""
    app.register_blueprint(api_bp, url_prefix='/api') 