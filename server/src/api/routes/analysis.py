from flask import Blueprint, request, jsonify
import json
import sys
import os
from datetime import datetime


from controllers.analysis_controller import AnalysisController

analysis_bp = Blueprint('analysis', __name__, url_prefix='/api/analysis')

analysis_controller = AnalysisController()

@analysis_bp.route('/generate', methods=['POST'])
def generate_analysis():
    """Generate hedge fund analysis based on provided parameters."""
    return analysis_controller.generate_analysis()

@analysis_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for analysis service."""
    return {
        'status': 'healthy',
        'service': 'analysis',
        'timestamp': datetime.now().isoformat()
    }, 200
