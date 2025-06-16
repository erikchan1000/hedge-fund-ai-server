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

def handle_analysis_request(request_data: AnalysisRequest) -> Response:
    """Handle the analysis request and return a streaming response."""
    try:
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
