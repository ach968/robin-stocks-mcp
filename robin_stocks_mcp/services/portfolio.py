# robin_stocks_mcp/services/portfolio.py
from typing import List, Optional
import robin_stocks.robinhood as rh
from robin_stocks_mcp.models import PortfolioSummary, Position
from robin_stocks_mcp.robinhood.client import RobinhoodClient
from robin_stocks_mcp.robinhood.errors import RobinhoodAPIError


class PortfolioService:
    """Service for portfolio operations."""
    
    def __init__(self, client: RobinhoodClient):
        self.client = client
    
    def get_portfolio_summary(self) -> PortfolioSummary:
        """Get portfolio summary."""
        self.client.ensure_session()
        
        try:
            account = rh.load_account_profile()
            
            return PortfolioSummary(
                equity=account.get('equity'),
                cash=account.get('cash'),
                buying_power=account.get('buying_power'),
                unrealized_pl=account.get('unsettled_debit'),
                day_change=account.get('portfolio_cash')
            )
        except Exception as e:
            raise RobinhoodAPIError(f"Failed to fetch portfolio: {e}")
    
    def get_positions(self, symbols: Optional[List[str]] = None) -> List[Position]:
        """Get portfolio positions, optionally filtered by symbols."""
        self.client.ensure_session()
        
        try:
            positions_data = rh.get_open_stock_positions()
            
            positions = []
            for item in positions_data:
                # Get symbol from instrument URL
                instrument = rh.get_instrument_by_url(item.get('instrument'))
                symbol = instrument.get('symbol') if instrument else None
                
                # Filter if symbols specified
                if symbols and symbol not in symbols:
                    continue
                
                position = Position(
                    symbol=symbol or 'UNKNOWN',
                    quantity=item.get('quantity'),
                    average_cost=item.get('average_buy_price'),
                    market_value=None,  # Would need quote lookup
                    unrealized_pl=None  # Would need calculation
                )
                positions.append(position)
            
            return positions
        except Exception as e:
            raise RobinhoodAPIError(f"Failed to fetch positions: {e}")
