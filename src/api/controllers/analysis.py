from typing import Dict, Any
from flask import request, jsonify, Response
from ..models.analysis import AnalysisRequest
from ..models.portfolio import Portfolio, Position, RealizedGains
from ..services.analysis import process_analysis_request

def handle_analysis_request(request_data: AnalysisRequest = None) -> Response:
    """Handle the analysis request and return the response."""
    try:
        if request_data is None:
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
            except TypeError as e:
                return jsonify({'error': f'Invalid request parameters: {str(e)}'}), 400
        
        result = process_analysis_request(request_data)
        return jsonify(result)
        
    except ValueError as e:
        return jsonify({'error': f'Invalid input value: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500 