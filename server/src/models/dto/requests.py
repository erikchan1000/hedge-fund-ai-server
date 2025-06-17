from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from ..domain.portfolio import Portfolio

@dataclass
class AnalysisRequestDTO:
    """Data Transfer Object for analysis requests."""
    
    tickers: List[str]
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    initial_cash: float = 100000.0
    margin_requirement: float = 0.0
    portfolio: Optional[Portfolio] = None
    show_reasoning: bool = False
    selected_analysts: Optional[List[str]] = None
    model_name: str = "gpt-4o"
    model_provider: str = "OpenAI"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisRequestDTO':
        """Create DTO from dictionary data."""
        # Handle portfolio conversion if present
        portfolio = None
        if 'portfolio' in data and data['portfolio']:
            portfolio_data = data['portfolio']
            if isinstance(portfolio_data, dict):
                portfolio = Portfolio.from_dict(portfolio_data)
            else:
                portfolio = portfolio_data
        
        return cls(
            tickers=data.get('tickers', []),
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            initial_cash=data.get('initial_cash', 100000.0),
            margin_requirement=data.get('margin_requirement', 0.0),
            portfolio=portfolio,
            show_reasoning=data.get('show_reasoning', False),
            selected_analysts=data.get('selected_analysts'),
            model_name=data.get('model_name', 'gpt-4o'),
            model_provider=data.get('model_provider', 'OpenAI')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert DTO to dictionary."""
        result = {
            'tickers': self.tickers,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'initial_cash': self.initial_cash,
            'margin_requirement': self.margin_requirement,
            'show_reasoning': self.show_reasoning,
            'selected_analysts': self.selected_analysts,
            'model_name': self.model_name,
            'model_provider': self.model_provider
        }
        
        if self.portfolio:
            result['portfolio'] = self.portfolio.to_dict()
        
        return result 