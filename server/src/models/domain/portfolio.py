from typing import Dict, Any, List
from dataclasses import dataclass, field

@dataclass
class Position:
    """Represents a trading position."""
    long: int = 0
    short: int = 0
    long_cost_basis: float = 0.0
    short_cost_basis: float = 0.0
    short_margin_used: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'long': self.long,
            'short': self.short,
            'long_cost_basis': self.long_cost_basis,
            'short_cost_basis': self.short_cost_basis,
            'short_margin_used': self.short_margin_used
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Position':
        return cls(
            long=data.get('long', 0),
            short=data.get('short', 0),
            long_cost_basis=data.get('long_cost_basis', 0.0),
            short_cost_basis=data.get('short_cost_basis', 0.0),
            short_margin_used=data.get('short_margin_used', 0.0)
        )

@dataclass
class RealizedGains:
    """Represents realized gains from trading."""
    long: float = 0.0
    short: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'long': self.long,
            'short': self.short
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RealizedGains':
        return cls(
            long=data.get('long', 0.0),
            short=data.get('short', 0.0)
        )

@dataclass
class Portfolio:
    """Represents a trading portfolio."""
    cash: float
    margin_requirement: float = 0.0
    margin_used: float = 0.0
    positions: Dict[str, Position] = field(default_factory=dict)
    realized_gains: Dict[str, RealizedGains] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'cash': self.cash,
            'margin_requirement': self.margin_requirement,
            'margin_used': self.margin_used,
            'positions': {
                ticker: position.to_dict()
                for ticker, position in self.positions.items()
            },
            'realized_gains': {
                ticker: gains.to_dict()
                for ticker, gains in self.realized_gains.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Portfolio':
        positions = {}
        if 'positions' in data:
            positions = {
                ticker: Position.from_dict(pos_data)
                for ticker, pos_data in data['positions'].items()
            }
        
        realized_gains = {}
        if 'realized_gains' in data:
            realized_gains = {
                ticker: RealizedGains.from_dict(gains_data)
                for ticker, gains_data in data['realized_gains'].items()
            }
        
        return cls(
            cash=data.get('cash', 0.0),
            margin_requirement=data.get('margin_requirement', 0.0),
            margin_used=data.get('margin_used', 0.0),
            positions=positions,
            realized_gains=realized_gains
        )
    
    @classmethod
    def create_empty(
        cls, 
        tickers: List[str], 
        initial_cash: float = 100000.0, 
        margin_requirement: float = 0.0
    ) -> 'Portfolio':
        """Create an empty portfolio for the given tickers."""
        positions = {
            ticker: Position()
            for ticker in tickers
        }
        realized_gains = {
            ticker: RealizedGains()
            for ticker in tickers
        }
        
        return cls(
            cash=initial_cash,
            margin_requirement=margin_requirement,
            margin_used=0.0,
            positions=positions,
            realized_gains=realized_gains
        ) 