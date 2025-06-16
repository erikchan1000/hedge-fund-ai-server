from flask import Blueprint, request
from .controllers.analysis import handle_analysis_request
from server.src.models.analysis import AnalysisRequest, Portfolio, RealizedGains, Position
from server.src.utils.logging import logger
from flask import jsonify

api_bp = Blueprint('api', __name__)

@api_bp.route('/generate_analysis', methods=['POST'])
def generate_analysis():
    """Generate hedge fund analysis based on provided parameters."""
    data = request.get_json()
    if 'portfolio' in data and isinstance(data['portfolio'], dict):
        portfolio_data = data['portfolio']
        if 'positions' in portfolio_data:
            portfolio_data['positions'] = {
                ticker: Position(**pos_data) 
                for ticker, pos_data in portfolio_data['positions'].items()
            }
        if 'realized_gains' in portfolio_data:
            portfolio_data['realized_gains'] = {
                ticker: RealizedGains(**gains_data)
                for ticker, gains_data in portfolio_data['realized_gains'].items()
            }
        data['portfolio'] = Portfolio(**portfolio_data)
    try:
        request_data = AnalysisRequest(**data)
        logger.debug("Successfully created AnalysisRequest")
    except TypeError as e:
        logger.error(f"Invalid request parameters: {str(e)}")
        return jsonify({'error': f'Invalid request parameters: {str(e)}'}), 400
        
    return handle_analysis_request(request_data) 