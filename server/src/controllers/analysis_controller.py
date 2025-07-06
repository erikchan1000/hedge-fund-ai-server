from typing import Dict, Any
from flask import request, jsonify, Response, stream_with_context
from src.services.analysis_service import AnalysisService
from src.models.dto.requests import AnalysisRequestDTO
from src.core.exceptions import ValidationError, BusinessLogicError
from src.utils.validators import validate_analysis_request
from src.utils.cancellation import cancellable_request, CancellationException
import logging
import json
from datetime import datetime

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
            
            def generate():
                try:
                    # Use cancellable request context
                    with cancellable_request() as cancellation_token:
                        initial_progress = {
                            "type": "progress",
                            "stage": "initialization",
                            "message": "Starting analysis...",
                            "progress": 0,
                            "timestamp": datetime.now().isoformat(),
                            "request_id": cancellation_token.request_id
                        }
                        print(f"initial_progress: {initial_progress}")
                        yield f"data: {json.dumps(initial_progress)}\n\n".encode('utf-8')
                        
                        # Get the analysis stream with cancellation token
                        response_stream = self.analysis_service.process_analysis_request(request_dto, cancellation_token)
                        
                        # Yield each chunk immediately in SSE format
                        for chunk in response_stream:
                            if isinstance(chunk, str):
                                # Convert JSON string to SSE format
                                yield f"data: {chunk.strip()}\n\n".encode('utf-8')
                            else:
                                yield f"data: {str(chunk).strip()}\n\n".encode('utf-8')
                        
                except CancellationException as e:
                    logger.info(f"Analysis request was cancelled: {str(e)}")
                    cancellation_event = {
                        "type": "cancelled",
                        "message": "Analysis was cancelled",
                        "timestamp": datetime.now().isoformat()
                    }
                    yield f"data: {json.dumps(cancellation_event)}\n\n".encode('utf-8')
                except Exception as e:
                    logger.error(f"Error in streaming: {str(e)}")
                    error_event = {
                        "type": "error",
                        "message": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
                    yield f"data: {json.dumps(error_event)}\n\n".encode('utf-8')
            
            # Create Flask Response with generator
            return Response(
                stream_with_context(generate()),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'X-Accel-Buffering': 'no',
                    'Connection': 'keep-alive',
                    'Access-Control-Allow-Origin': '*',
                    'Transfer-Encoding': 'chunked'
                },
                direct_passthrough=True
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