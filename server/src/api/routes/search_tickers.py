from flask import Blueprint, request, jsonify
from external.clients.polygon_client import PolygonClient

search_tickers_bp = Blueprint('search_tickers', __name__, url_prefix='/api/search_tickers')
polygon_client = PolygonClient()

@search_tickers_bp.route('', methods=['GET'])
def search_tickers():
    query = request.args.get('query', '')
    if not query:
        return jsonify({'error': 'Missing query parameter'}), 400
    results = polygon_client.search_tickers(query)
    return jsonify({'results': results}) 