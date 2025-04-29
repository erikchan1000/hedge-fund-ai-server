from flask import Flask
from api import init_app
from main import create_workflow

def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    # Initialize the workflow before starting the server
    create_workflow()
    init_app(app)
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True) 