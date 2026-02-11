# robin_stocks_mcp/services/watchlists.py
from typing import List
import robin_stocks.robinhood as rh
from robin_stocks_mcp.models import Watchlist
from robin_stocks_mcp.robinhood.client import RobinhoodClient
from robin_stocks_mcp.robinhood.errors import RobinhoodAPIError


class WatchlistsService:
    """Service for watchlist operations."""
    
    def __init__(self, client: RobinhoodClient):
        self.client = client
    
    def get_watchlists(self) -> List[Watchlist]:
        """Get all watchlists."""
        self.client.ensure_session()
        
        try:
            watchlists_data = rh.get_all_watchlists()
            
            watchlists = []
            for item in watchlists_data:
                watchlist = Watchlist(
                    id=item.get('url', '').split('/')[-2] if item.get('url') else '',
                    name=item.get('name', ''),
                    symbols=[]  # Would need to fetch symbols separately
                )
                watchlists.append(watchlist)
            
            return watchlists
        except Exception as e:
            raise RobinhoodAPIError(f"Failed to fetch watchlists: {e}")
