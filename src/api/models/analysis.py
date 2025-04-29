from dataclasses import dataclass
from typing import List, Optional
from .portfolio import Portfolio

@dataclass
class AnalysisRequest:
    tickers: List[str]
    initial_cash: float
    margin_requirement: float = 0.0
    show_reasoning: bool = False
    show_agent_graph: bool = False
    use_ollama: bool = False
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    selected_analysts: Optional[List[str]] = None
    model_name: str = 'gpt-4'
    model_provider: str = 'OpenAI'
    portfolio: Optional[Portfolio] = None 