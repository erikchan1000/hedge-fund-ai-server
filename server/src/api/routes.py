from flask import Blueprint
from .controllers.analysis import handle_analysis_request, handle_test_stream

api_bp = Blueprint('api', __name__)

@api_bp.route('/generate_analysis', methods=['POST'])
def generate_analysis():
    """Generate hedge fund analysis based on provided parameters."""
    return handle_analysis_request()

@api_bp.route('/test_stream', methods=['GET'])
def test_stream():
    """Test streaming endpoint to verify streaming functionality."""
    return handle_test_stream() 