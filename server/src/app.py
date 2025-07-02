from flask import Flask
from api import init_app
import os
from werkzeug.middleware.proxy_fix import ProxyFix

def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Configure for streaming
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['PROPAGATE_EXCEPTIONS'] = True
    
    # Add security headers
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        # Ensure streaming headers are set
        if 'text/plain' in response.content_type:
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Connection'] = 'keep-alive'
            response.headers['X-Accel-Buffering'] = 'no'
            # Force immediate flushing
            response.headers['Transfer-Encoding'] = 'chunked'
        return response
    
    # Handle proxy headers
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    
    init_app(app)
    return app

if __name__ == '__main__':
    app = create_app()
    
    # Use port 80 for HTTP or 443 for HTTPS
    port = int(os.environ.get('PORT', 80))
    
    # Run the Flask app with streaming enabled
    app.run(host='0.0.0.0', port=port, threaded=True) 