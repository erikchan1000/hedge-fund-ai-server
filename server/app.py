from flask import Flask
from src.api import init_app
from src.utils.cancellation import get_cancellation_manager
import os
import signal
import atexit
from werkzeug.middleware.proxy_fix import ProxyFix
import logging

logger = logging.getLogger(__name__)

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
    
    # Setup graceful shutdown
    def shutdown_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        cleanup_resources()
        exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    
    # Register cleanup function to run on exit
    atexit.register(cleanup_resources)
    
    return app

def cleanup_resources():
    """Clean up application resources."""
    try:
        logger.info("Cleaning up application resources...")
        
        # Cancel all active requests
        cancellation_manager = get_cancellation_manager()
        cancellation_manager.shutdown()
        
        logger.info("Resource cleanup completed")
    except Exception as e:
        logger.error(f"Error during resource cleanup: {e}")

if __name__ == '__main__':
    app = create_app()
    
    # Use port 80 for HTTP or 443 for HTTPS
    port = int(os.environ.get('PORT', 80))
    
    try:
        # Run the Flask app with streaming enabled
        app.run(host='0.0.0.0', port=port, threaded=True)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
        cleanup_resources()
    except Exception as e:
        logger.error(f"Error running Flask app: {e}")
        cleanup_resources()
        raise 