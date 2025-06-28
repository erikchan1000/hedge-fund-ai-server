from flask import Blueprint, jsonify

portfolio_bp = Blueprint('portfolio', __name__, url_prefix='/api/portfolio')

@portfolio_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for portfolio service."""
    return {'status': 'healthy', 'service': 'portfolio'}, 200

@portfolio_bp.route('/status', methods=['GET'])
def get_portfolio_status():
    """Get portfolio status - placeholder for future implementation."""
    return {
        'message': 'Portfolio service is operational',
        'endpoints': [
            'GET /api/portfolio/health',
            'GET /api/portfolio/status'
        ]
    }, 200 