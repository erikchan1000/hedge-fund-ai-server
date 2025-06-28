from flask import Blueprint, jsonify
from datetime import datetime

docs_bp = Blueprint('docs', __name__, url_prefix='/api')

@docs_bp.route('/', methods=['GET'])
@docs_bp.route('/docs', methods=['GET'])
def api_documentation():
    """API documentation endpoint."""
    return {
        'name': 'AI Hedge Fund API',
        'version': '1.0.0',
        'architecture': 'Model-Controller-Service (MCS)',
        'timestamp': datetime.now().isoformat(),
        'endpoints': {
            'analysis': {
                'POST /api/analysis/generate': {
                    'description': 'Generate hedge fund analysis',
                    'content_type': 'application/json',
                    'required_fields': ['tickers'],
                    'optional_fields': [
                        'start_date', 'end_date', 'initial_cash', 
                        'margin_requirement', 'show_reasoning',
                        'selected_analysts', 'model_name', 'model_provider'
                    ]
                },
                'GET /api/analysis/health': {
                    'description': 'Analysis service health check',
                    'returns': 'Service health status'
                }
            },
            'portfolio': {
                'GET /api/portfolio/health': {
                    'description': 'Portfolio service health check',
                    'returns': 'Service health status'
                },
                'GET /api/portfolio/status': {
                    'description': 'Portfolio service status',
                    'returns': 'Service operational status'
                }
            },
            'system': {
                'GET /api/health': {
                    'description': 'System-wide health check',
                    'returns': 'Overall system health'
                },
                'GET /api/status': {
                    'description': 'Comprehensive system status',
                    'returns': 'Detailed system information'
                },
                'GET /api/docs': {
                    'description': 'API documentation',
                    'returns': 'This documentation'
                }
            },
            'legacy': {
                'POST /api/legacy/generate_analysis': {
                    'description': 'DEPRECATED - Redirects to /api/analysis/generate',
                    'status': 'deprecated'
                },
                'GET /api/legacy/health': {
                    'description': 'DEPRECATED - Redirects to /api/health',
                    'status': 'deprecated'
                }
            }
        },
        'example_request': {
            'url': '/api/analysis/generate',
            'method': 'POST',
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': {
                'tickers': ['AAPL', 'MSFT'],
                'start_date': '2023-01-01',
                'end_date': '2023-12-31',
                'initial_cash': 100000,
                'show_reasoning': True,
                'selected_analysts': ['warren_buffett', 'peter_lynch'],
                'model_name': 'gpt-4o',
                'model_provider': 'OpenAI'
            }
        },
        'response_format': {
            'streaming': True,
            'content_type': 'application/json',
            'events': ['progress', 'result', 'error']
        }
    }, 200 