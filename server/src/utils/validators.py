from typing import Dict, Any, List

def validate_analysis_request(data: Dict[str, Any]) -> List[str]:
    """Validate analysis request data structure."""
    errors = []
    
    # Check required fields
    if not data.get('tickers'):
        errors.append("Field 'tickers' is required")
    elif not isinstance(data['tickers'], list):
        errors.append("Field 'tickers' must be a list")
    
    # Validate optional fields if present
    if 'start_date' in data and data['start_date'] is not None:
        if not isinstance(data['start_date'], str):
            errors.append("Field 'start_date' must be a string")
    
    if 'end_date' in data and data['end_date'] is not None:
        if not isinstance(data['end_date'], str):
            errors.append("Field 'end_date' must be a string")
    
    if 'initial_cash' in data:
        if not isinstance(data['initial_cash'], (int, float)):
            errors.append("Field 'initial_cash' must be a number")
    
    if 'margin_requirement' in data:
        if not isinstance(data['margin_requirement'], (int, float)):
            errors.append("Field 'margin_requirement' must be a number")
    
    if 'show_reasoning' in data:
        if not isinstance(data['show_reasoning'], bool):
            errors.append("Field 'show_reasoning' must be a boolean")
    
    if 'selected_analysts' in data and data['selected_analysts'] is not None:
        if not isinstance(data['selected_analysts'], list):
            errors.append("Field 'selected_analysts' must be a list")
    
    if 'model_name' in data:
        if not isinstance(data['model_name'], str):
            errors.append("Field 'model_name' must be a string")
    
    if 'model_provider' in data:
        if not isinstance(data['model_provider'], str):
            errors.append("Field 'model_provider' must be a string")
    
    return errors 