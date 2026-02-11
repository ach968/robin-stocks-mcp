# robin_stocks_mcp/services/options.py
import logging
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

logger = logging.getLogger(__name__)


class OptionsService:
    """Service for options operations."""

    def __init__(self, client: RobinhoodClient):
        self.client = client

    def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current stock price for near-the-money filtering."""
        try:
            prices = rh.get_latest_price(symbol)
            if prices and prices[0]:
                return float(prices[0])
        except Exception:
            pass
        return None

    @staticmethod
    def _build_contract(item: dict, symbol: str, expiration: str) -> OptionContract:
        """Build an OptionContract from a robin_stocks option dict.

        The ``item`` dict is expected to come from robin_stocks helpers such as
        ``find_options_by_expiration`` which merge instrument data with market
        data (greeks, bid/ask, volume, etc.).
        """
        return OptionContract(
            symbol=item.get("chain_symbol", symbol),
            expiration=item.get("expiration_date", expiration),
            strike=item.get("strike_price"),
            type="call" if item.get("type") == "call" else "put",
            bid=item.get("bid_price"),
            ask=item.get("ask_price"),
            mark_price=item.get("adjusted_mark_price") or item.get("mark_price"),
            last_trade_price=item.get("last_trade_price"),
            open_interest=item.get("open_interest"),
            volume=item.get("volume"),
            implied_volatility=item.get("implied_volatility"),
            delta=item.get("delta"),
            gamma=item.get("gamma"),
            theta=item.get("theta"),
            vega=item.get("vega"),
            rho=item.get("rho"),
            chance_of_profit_short=item.get("chance_of_profit_short"),
            chance_of_profit_long=item.get("chance_of_profit_long"),
        )

    def get_options_chain(
        self,
        symbol: str,
        expiration_date: Optional[str] = None,
        option_type: Optional[str] = None,
        strike_price: Optional[str] = None,
    ) -> List[OptionContract]:
        """Get options chain for a symbol.

        Args:
            symbol: Stock ticker symbol.
            expiration_date: Expiration date (YYYY-MM-DD). Uses nearest if not provided.
            option_type: 'call' or 'put'. Filters to one side of the chain.
            strike_price: Specific strike price to look up. When provided,
                          returns 1-2 contracts with full market data (greeks).
        """
        if not symbol:
            raise InvalidArgumentError("Symbol is required")

        self.client.ensure_session()

        try:
            # Resolve expiration date if not provided
            if not expiration_date:
                chains_data = rh.get_chains(symbol)
                if not chains_data or not isinstance(chains_data, dict):
                    return []
                expirations = chains_data.get("expiration_dates", [])
                if not expirations:
                    return []
                expiration_date = str(expirations[0])

            exp = str(expiration_date)  # guaranteed non-None str from here

            # Targeted lookup: specific strike + expiration (fast, includes greeks)
            if strike_price:
                options_data = rh.find_options_by_expiration_and_strike(
                    symbol,
                    expirationDate=exp,
                    strikePrice=str(strike_price),
                    optionType=option_type,
                )
                contracts: List[OptionContract] = []
                if not options_data:
                    return contracts
                for item in options_data:
                    if not item or not isinstance(item, dict):
                        continue
                    contracts.append(self._build_contract(item, symbol, exp))
                return contracts

            # Chain lookup: all strikes for an expiration
            # find_options_by_expiration fetches market data per-contract (slow
            # for large chains). To keep response times reasonable we:
            # 1. Always pass optionType to halve the contracts
            # 2. Filter to near-the-money strikes (±20% of current price)
            options_data = rh.find_options_by_expiration(
                symbol,
                expirationDate=exp,
                optionType=option_type,
            )

            if not options_data:
                return []

            # Near-the-money filtering
            current_price = self._get_current_price(symbol)

            contracts = []
            for item in options_data:
                if not item or not isinstance(item, dict):
                    continue

                # Filter to near-the-money if we have a current price
                if current_price:
                    try:
                        strike_val = float(item.get("strike_price", 0))
                        lower = current_price * 0.80
                        upper = current_price * 1.20
                        if strike_val < lower or strike_val > upper:
                            continue
                    except (ValueError, TypeError):
                        pass

                contracts.append(self._build_contract(item, symbol, exp))

            return contracts

            # Chain lookup: all strikes for an expiration
            # find_options_by_expiration fetches market data per-contract (slow
            # for large chains). To keep response times reasonable we:
            # 1. Always pass optionType to halve the contracts
            # 2. Filter to near-the-money strikes (±20% of current price)
            options_data = rh.find_options_by_expiration(
                symbol,
                expirationDate=expiration_date,
                optionType=option_type,
            )

            # Near-the-money filtering
            current_price = self._get_current_price(symbol)

            contracts = []
            for item in options_data:
                if item is None:
                    continue

                # Filter to near-the-money if we have a current price
                if current_price:
                    try:
                        strike = float(item.get("strike_price", 0))
                        lower = current_price * 0.80
                        upper = current_price * 1.20
                        if strike < lower or strike > upper:
                            continue
                    except (ValueError, TypeError):
                        pass

                contracts.append(self._build_contract(item, symbol, expiration_date))

            return contracts

        except (RobinhoodAPIError, InvalidArgumentError, AuthRequiredError):
            raise
        except (requests.RequestException, ConnectionError, TimeoutError) as e:
            raise RobinhoodAPIError(f"Failed to fetch options chain: {e}") from e
        except Exception as e:
            raise RobinhoodAPIError(f"Failed to fetch options chain: {e}") from e
