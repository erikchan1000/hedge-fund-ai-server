from typing import Dict, Any, Generator
from flask import request, jsonify, Response, stream_with_context
from ..models.analysis import AnalysisRequest
from ..models.portfolio import Portfolio, Position, RealizedGains
from ..services.analysis import process_analysis_request
from main import create_workflow
from datetime import datetime
import logging
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def generate_stream(request_data: AnalysisRequest) -> Generator[str, None, None]:
    """Generate a stream of analysis data and progress updates."""
    try:
        logger.debug("Starting stream generation")
        # Create a new workflow for this request
        workflow = create_workflow()
        logger.debug("Workflow created")
        
        # Process the request and stream the results
        logger.debug("Starting to process analysis request")
        for result in process_analysis_request(request_data):
            if result is None:
                logger.warning("Received None result from process_analysis_request")
                continue
                
            # Add timestamp to each event
            event = {
                **result,
                "timestamp": datetime.now().isoformat()
            }
            # Send as raw JSON
            yield json.dumps(event) + "\n"
            
    except Exception as e:
        logger.error(f"Error in stream generation: {str(e)}", exc_info=True)
        error_event = {
            "type": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }
        yield json.dumps(error_event) + "\n"

def handle_analysis_request(request_data: AnalysisRequest = None) -> Response:
    """Handle the analysis request and return a streaming response."""
    try:
        logger.debug("Handling analysis request")
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
                logger.debug("Successfully created AnalysisRequest")
            except TypeError as e:
                logger.error(f"Invalid request parameters: {str(e)}")
                return jsonify({'error': f'Invalid request parameters: {str(e)}'}), 400
        
        def stream():
            logger.debug("Starting stream")
            for chunk in generate_stream(request_data):
                yield chunk
            logger.debug("Stream completed")

        return Response(
            stream(),
            mimetype='application/json',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no',
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        )
        
    except Exception as e:
        logger.error(f"Error in request handling: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500 