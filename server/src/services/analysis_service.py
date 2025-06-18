from typing import Dict, Any, List, Generator
from datetime import datetime, timedelta
import json
import logging

from models.dto.requests import AnalysisRequestDTO
from models.dto.responses import AnalysisProgressDTO, AnalysisResultDTO
from models.domain.portfolio import Portfolio
from services.workflow_service import WorkflowService
from services.validation_service import ValidationService
from core.exceptions import ValidationError

logger = logging.getLogger(__name__)

class AnalysisService:
    """Service for handling analysis business logic."""
    
    def __init__(self):
        self.workflow_service = WorkflowService()
        self.validation_service = ValidationService()
    
    def process_analysis_request(self, request_dto: AnalysisRequestDTO) -> Generator[str, None, None]:
        """Process analysis request and yield streaming results."""
        try:
            # Validate business rules
            self.validation_service.validate_analysis_request(request_dto)
            
            # Process dates
            end_date = request_dto.end_date or datetime.now().strftime('%Y-%m-%d')
            start_date = self._calculate_start_date(request_dto.start_date, end_date)
            
            # Prepare portfolio
            portfolio = self._prepare_portfolio(request_dto)
            
            # Generate analysis stream
            yield from self._generate_analysis_stream(
                request_dto, start_date, end_date, portfolio
            )
            
        except Exception as e:
            logger.error(f"Error in analysis processing: {str(e)}", exc_info=True)
            error_event = {
                "type": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
            yield json.dumps(error_event) + "\n"
    
    def _calculate_start_date(self, start_date: str, end_date: str) -> str:
        """Calculate start date if not provided."""
        if start_date:
            if not self.validation_service.validate_date(start_date):
                raise ValidationError('Invalid start_date format. Use YYYY-MM-DD')
            return start_date
        
        # Default to 3 months before end date
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        return (end_date_obj - timedelta(days=90)).strftime('%Y-%m-%d')
    
    def _prepare_portfolio(self, request_dto: AnalysisRequestDTO) -> Dict[str, Any]:
        """Prepare portfolio data for analysis."""
        if request_dto.portfolio:
            return request_dto.portfolio.to_dict()
        
        # Create empty portfolio
        return Portfolio.create_empty(
            request_dto.tickers,
            request_dto.initial_cash,
            request_dto.margin_requirement
        ).to_dict()
    
    def _generate_analysis_stream(
        self, 
        request_dto: AnalysisRequestDTO,
        start_date: str,
        end_date: str,
        portfolio: Dict[str, Any]
    ) -> Generator[str, None, None]:
        """Generate streaming analysis results."""
        
        # Initial progress
        progress_dto = AnalysisProgressDTO(
            type="progress",
            stage="initialization",
            message="Starting analysis...",
            progress=0,
            analysts=request_dto.selected_analysts or [],
            tickers=request_dto.tickers
        )
        yield json.dumps(progress_dto.to_dict()) + "\n"
        
        # Execute analysis workflow
        yield from self.workflow_service.execute_analysis_workflow(
            tickers=request_dto.tickers,
            start_date=start_date,
            end_date=end_date,
            portfolio=portfolio,
            selected_analysts=request_dto.selected_analysts or [],
            show_reasoning=request_dto.show_reasoning,
            model_name=request_dto.model_name,
            model_provider=request_dto.model_provider
        ) 