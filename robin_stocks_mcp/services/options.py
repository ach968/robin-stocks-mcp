# robin_stocks_mcp/services/options.py
from typing import List, Optional
import requests
import robin_stocks.robinhood as rh
from robin_stocks_mcp.models import OptionContract
from robin_stocks_mcp.robinhood.client import RobinhoodClient
from robin_stocks_mcp.robinhood.errors import (
    AuthRequiredError,
    InvalidArgumentError,
    RobinhoodAPIError,
)


class OptionsService:
    """Service for options operations."""

    def __init__(self, client: RobinhoodClient):
        self.client = client

    def get_options_chain(
        self, symbol: str, expiration_date: Optional[str] = None
    ) -> List[OptionContract]:
        """Get options chain for a symbol."""
        if not symbol:
            raise InvalidArgumentError("Symbol is required")

        self.client.ensure_session()

        try:
            # Get available expiration dates if not specified
            if expiration_date:
                expirations = [expiration_date]
            else:
                chains = rh.get_chains(symbol)
                expirations = chains.get("expiration_dates", [])
                if not expirations:
                    return []
                # Use nearest expiration
                expirations = [expirations[0]]

            contracts = []
            for exp in expirations:
                options_data = rh.find_options_by_expiration(symbol, expirationDate=exp)

                for item in options_data:
                    contract = OptionContract(
                        symbol=item.get("chain_symbol", symbol),
                        expiration=exp,
                        strike=item.get("strike_price"),
                        type="call" if item.get("type") == "call" else "put",
                        bid=item.get("bid_price"),
                        ask=item.get("ask_price"),
                        open_interest=item.get("open_interest"),
                        volume=item.get("volume"),
                    )
                    contracts.append(contract)

            return contracts
        except (RobinhoodAPIError, InvalidArgumentError, AuthRequiredError):
            raise
        except (requests.RequestException, ConnectionError, TimeoutError) as e:
            raise RobinhoodAPIError(f"Failed to fetch options chain: {e}") from e
        except Exception as e:
            raise RobinhoodAPIError(f"Failed to fetch options chain: {e}") from e
