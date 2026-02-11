# robin_stocks_mcp/services/fundamentals.py
from typing import Optional
import robin_stocks.robinhood as rh
from robin_stocks_mcp.models import Fundamentals
from robin_stocks_mcp.robinhood.client import RobinhoodClient
from robin_stocks_mcp.robinhood.errors import InvalidArgumentError, RobinhoodAPIError


class FundamentalsService:
    """Service for fundamentals operations."""
    
    def __init__(self, client: RobinhoodClient):
        self.client = client
    
    def get_fundamentals(self, symbol: str) -> Fundamentals:
        """Get fundamentals for a symbol."""
        if not symbol:
            raise InvalidArgumentError("Symbol is required")
        
        self.client.ensure_session()
        
        try:
            data = rh.get_fundamentals(symbol)
            
            if isinstance(data, list) and len(data) > 0:
                data = data[0]
            
            return Fundamentals(
                market_cap=data.get('market_cap'),
                pe_ratio=data.get('pe_ratio'),
                dividend_yield=data.get('dividend_yield'),
                week_52_high=data.get('high_52_weeks'),
                week_52_low=data.get('low_52_weeks')
            )
        except Exception as e:
            raise RobinhoodAPIError(f"Failed to fetch fundamentals: {e}")
