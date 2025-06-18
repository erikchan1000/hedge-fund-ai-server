from flask import Blueprint, jsonify
from datetime import datetime

# Create blueprint
health_bp = Blueprint('health', __name__, url_prefix='/api')

@health_bp.route('/health', methods=['GET'])
def system_health():
    """System-wide health check endpoint."""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'ai-hedge-fund',
        'version': '1.0.0',
        'components': {
            'analysis_service': 'healthy',
            'portfolio_service': 'healthy',
            'workflow_service': 'healthy'
        }
    }, 200

@health_bp.route('/status', methods=['GET'])
def system_status():
    """Get comprehensive system status."""
    return {
        'status': 'operational',
        'timestamp': datetime.now().isoformat(),
        'api_version': '1.0.0',
        'endpoints': {
            'analysis': '/api/analysis/generate',
            'health': '/api/health',
            'portfolio': '/api/portfolio/status'
        },
        'architecture': 'Model-Controller-Service (MCS)',
        'documentation': 'https://github.com/your-repo/ai-hedge-fund'
    }, 200 