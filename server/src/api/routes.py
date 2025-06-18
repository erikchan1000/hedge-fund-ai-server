"""Legacy API routes - DEPRECATED. Use new routes in api/routes/ directory."""

from flask import Blueprint, redirect, url_for

api_bp = Blueprint('api', __name__)

# Legacy route - redirects to new endpoint
@api_bp.route('/generate_analysis', methods=['POST'])
def generate_analysis_legacy():
    """Legacy endpoint - redirects to new analysis endpoint."""
    return redirect(url_for('analysis.generate_analysis'), code=308) 