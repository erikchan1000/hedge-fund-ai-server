from flask import Blueprint, Response, stream_with_context
import json
import sys
import os
from datetime import datetime
import time
from src.controllers.analysis_controller import AnalysisController


analysis_bp = Blueprint('analysis', __name__, url_prefix='/api/analysis')

analysis_controller = AnalysisController()

@analysis_bp.route('/generate', methods=['POST'])
def generate_analysis():
    """Generate hedge fund analysis based on provided parameters."""
    return analysis_controller.generate_analysis()

@analysis_bp.route('/test-stream', methods=['GET'])
def test_stream():
    def generate():
        for i in range(10):
            data = {
                "type": "progress",
                "message": f"Test message {i+1}",
                "progress": (i+1) * 10,
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(data)}\n\n".encode('utf-8')
            sys.stdout.flush()
            time.sleep(1)

        final = {
            "type": "result",
            "data": {"message": "Streaming test completed"},
            "timestamp": datetime.now().isoformat()
        }
        yield f"data: {json.dumps(final)}\n\n".encode('utf-8')

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

@analysis_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for analysis service."""
    return {
        'status': 'healthy',
        'service': 'analysis',
        'timestamp': datetime.now().isoformat()
    }, 200
