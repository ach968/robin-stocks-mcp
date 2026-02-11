# robin_stocks_mcp/services/watchlists.py
from typing import List
import requests
import robin_stocks.robinhood as rh
from robin_stocks_mcp.models import Watchlist
from robin_stocks_mcp.robinhood.client import RobinhoodClient
from robin_stocks_mcp.robinhood.errors import (
    AuthRequiredError,
    InvalidArgumentError,
    RobinhoodAPIError,
)


class WatchlistsService:
    """Service for watchlist operations."""

    def __init__(self, client: RobinhoodClient):
        self.client = client

    def get_watchlists(self) -> List[Watchlist]:
        """Get all watchlists with their symbols."""
        self.client.ensure_session()

        try:
            watchlists_data = rh.get_all_watchlists()

            # get_all_watchlists() returns a dict with a 'results' key.
            # Each result has 'id' and 'display_name' fields.
            results = (
                watchlists_data.get("results", [])
                if isinstance(watchlists_data, dict)
                else []
            )

            watchlists = []
            for item in results:
                wl_id = item.get("id", "")
                wl_name = item.get("display_name", "")

                # Fetch instruments for this watchlist and resolve symbols
                symbols = self._get_watchlist_symbols(wl_name)

                watchlist = Watchlist(
                    id=wl_id,
                    name=wl_name,
                    symbols=symbols,
                )
                watchlists.append(watchlist)

            return watchlists
        except (RobinhoodAPIError, InvalidArgumentError, AuthRequiredError):
            raise
        except (requests.RequestException, ConnectionError, TimeoutError) as e:
            raise RobinhoodAPIError(f"Failed to fetch watchlists: {e}") from e
        except Exception as e:
            raise RobinhoodAPIError(f"Failed to fetch watchlists: {e}") from e

    def _get_watchlist_symbols(self, name: str) -> List[str]:
        """Fetch symbols for a watchlist by name."""
        try:
            items = rh.get_watchlist_by_name(name=name)
            if not items or not isinstance(items, list):
                return []

            symbols = []
            for entry in items:
                if not isinstance(entry, dict):
                    continue
                instrument_url = entry.get("instrument")
                if instrument_url:
                    symbol = rh.get_symbol_by_url(instrument_url)
                    if symbol:
                        symbols.append(symbol)
            return symbols
        except Exception:
            return []
