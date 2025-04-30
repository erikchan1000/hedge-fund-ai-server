from datetime import datetime, timedelta
from typing import Dict, Any, List, Generator
from main import run_hedge_fund, create_workflow
from ..models.portfolio import Portfolio
from ..models.analysis import AnalysisRequest
import time
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def validate_date(date_str: str) -> bool:
    """Validate if a string is in YYYY-MM-DD format."""
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def process_analysis_request(request_data: AnalysisRequest) -> Generator[Dict[str, Any], None, None]:
    """Process the analysis request and yield results incrementally."""
    tickers: List[str] = request_data.tickers
    app = create_workflow().compile()
    
    # Handle dates
    end_date: str = request_data.end_date or datetime.now().strftime('%Y-%m-%d')
    if not validate_date(end_date):
        raise ValueError('Invalid end_date format. Use YYYY-MM-DD')
        
    if request_data.start_date is None:
        # Calculate 3 months before end_date
        end_date_obj: datetime = datetime.strptime(end_date, '%Y-%m-%d')
        start_date: str = (end_date_obj - timedelta(days=90)).strftime('%Y-%m-%d')
    else:
        start_date = request_data.start_date
        if not validate_date(start_date):
            raise ValueError('Invalid start_date format. Use YYYY-MM-DD')
    
    portfolio: Portfolio = request_data.portfolio or Portfolio.create_empty(
        tickers,
        request_data.initial_cash,
        request_data.margin_requirement
    )
    
    portfolio_dict = {
        "cash": portfolio.cash,
        "margin_requirement": portfolio.margin_requirement,
        "margin_used": portfolio.margin_used,
        "positions": {
            ticker: vars(position)
            for ticker, position in portfolio.positions.items()
        },
        "realized_gains": {
            ticker: vars(gains)
            for ticker, gains in portfolio.realized_gains.items()
        }
    }
    
    # Run the hedge fund analysis and yield results as they come
    for result in run_hedge_fund(
        tickers=tickers,
        start_date=start_date,
        end_date=end_date,
        portfolio=portfolio_dict,
        app=app,
        show_reasoning=request_data.show_reasoning,
        selected_analysts=request_data.selected_analysts if request_data.selected_analysts else [],
        model_name=request_data.model_name,
        model_provider=request_data.model_provider,
    ):
        yield result