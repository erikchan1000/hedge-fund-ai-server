from flask import Blueprint
from .controllers.analysis import handle_analysis_request

api_bp = Blueprint('api', __name__)

@api_bp.route('/generate_analysis', methods=['POST'])
def generate_analysis():
    """Generate hedge fund analysis based on provided parameters."""
    return handle_analysis_request() 