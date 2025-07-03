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
