from dataclasses import dataclass
from typing import Dict, List

@dataclass
class Position:
    long: int = 0
    short: int = 0
    long_cost_basis: float = 0.0
    short_cost_basis: float = 0.0
    short_margin_used: float = 0.0

@dataclass
class RealizedGains:
    long: float = 0.0
    short: float = 0.0

@dataclass
class Portfolio:
    cash: float
    positions: Dict[str, Position]
    realized_gains: Dict[str, RealizedGains]
    margin_requirement: float = 0.0
    margin_used: float = 0.0

    @classmethod
    def create_empty(cls, tickers: List[str], initial_cash: float, margin_requirement: float = 0.0) -> 'Portfolio':
        """Create an empty portfolio with the given parameters."""
        return cls(
            cash=initial_cash,
            positions={ticker: Position() for ticker in tickers},
            realized_gains={ticker: RealizedGains() for ticker in tickers},
            margin_requirement=margin_requirement,
            margin_used=0.0
        ) 