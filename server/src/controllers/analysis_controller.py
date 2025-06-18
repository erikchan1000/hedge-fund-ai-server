from typing import Dict, Any
from flask import request, jsonify, Response
from services.analysis_service import AnalysisService
from models.dto.requests import AnalysisRequestDTO
from core.exceptions import ValidationError, BusinessLogicError
from utils.validators import validate_analysis_request
import logging

logger = logging.getLogger(__name__)

class AnalysisController:
    """Controller for handling analysis-related HTTP requests."""
    
    def __init__(self):
        self.analysis_service = AnalysisService()
    
    def generate_analysis(self) -> Response:
        """Handle analysis generation requests."""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            validation_errors = validate_analysis_request(data)
            if validation_errors:
                return jsonify({'errors': validation_errors}), 400
            
            request_dto = AnalysisRequestDTO.from_dict(data)
            
            response_stream = self.analysis_service.process_analysis_request(request_dto)
            
            return Response(
                response_stream,
                mimetype='application/json',
                headers={
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'X-Accel-Buffering': 'no',
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                }
            )
            
        except ValidationError as e:
            logger.warning(f"Validation error: {str(e)}")
            return jsonify({'error': str(e)}), 400
            
        except BusinessLogicError as e:
            logger.error(f"Business logic error: {str(e)}")
            return jsonify({'error': str(e)}), 422
            
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return jsonify({'error': 'Internal server error'}), 500 