# robin_stocks_mcp/services/options.py
import logging
from typing import List, Optional

import requests
import robin_stocks.robinhood as rh

from robin_stocks_mcp.models import OptionContract, OptionPosition
from robin_stocks_mcp.robinhood.client import RobinhoodClient
from robin_stocks_mcp.robinhood.errors import (
    AuthRequiredError,
    InvalidArgumentError,
    RobinhoodAPIError,
)

logger = logging.getLogger(__name__)


class OptionsService:
    """Service for options operations.

    Uses two strategies to keep response times within MCP timeout limits:

    1. **Chain listing** (no strike_price): ``find_tradable_options`` makes a
       single paginated API call to Robinhood.  This is fast but returns only
       instrument data (strike, type, expiration) — no bid/ask or greeks.

    2. **Targeted lookup** (strike_price provided): ``get_option_market_data``
       returns full market data (bid/ask, greeks, profitability) for the
       specific (symbol, expiration, strike, type) combination.

    The slow ``find_options_by_expiration`` helper is intentionally avoided
    because it makes one HTTP request *per contract* to fetch market data,
    which easily exceeds the 60-second MCP timeout for chains with many
    strikes.
    """

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
        """Build an OptionContract from a robin_stocks dict.

        Works with both instrument data (from ``find_tradable_options``)
        and market data (from ``get_option_market_data``).  Missing keys
        simply resolve to ``None`` thanks to ``.get()``.
        """
        return OptionContract(
            symbol=item.get("chain_symbol", symbol),
            expiration=item.get("expiration_date", expiration),
            strike=item.get("strike_price"),
            type="call" if item.get("type") == "call" else "put",
            bid=item.get("bid_price"),
            ask=item.get("ask_price"),
            mark_price=(item.get("adjusted_mark_price") or item.get("mark_price")),
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
            expiration_date: YYYY-MM-DD. Uses nearest if omitted.
            option_type: ``'call'`` or ``'put'``.
            strike_price: Specific strike price. When provided,
                returns 1-2 contracts with full greeks via
                ``get_option_market_data``.
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

            exp = str(expiration_date)

            # --- Targeted lookup (strike_price provided) ---
            # Uses get_option_market_data for full greeks.
            if strike_price:
                return self._targeted_lookup(symbol, exp, strike_price, option_type)

            # --- Chain listing (no strike_price) ---
            # Uses find_tradable_options (single paginated call).
            return self._chain_listing(symbol, exp, option_type)

        except (
            RobinhoodAPIError,
            InvalidArgumentError,
            AuthRequiredError,
        ):
            raise
        except (
            requests.RequestException,
            ConnectionError,
            TimeoutError,
        ) as e:
            raise RobinhoodAPIError(f"Failed to fetch options chain: {e}") from e
        except Exception as e:
            raise RobinhoodAPIError(f"Failed to fetch options chain: {e}") from e

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _targeted_lookup(
        self,
        symbol: str,
        exp: str,
        strike_price: str,
        option_type: Optional[str],
    ) -> List[OptionContract]:
        """Fetch market data for a specific strike.

        If ``option_type`` is given, returns one contract.
        Otherwise returns both call and put at that strike.
        """
        contracts: List[OptionContract] = []

        types_to_fetch: List[str] = [option_type] if option_type else ["call", "put"]

        for ot in types_to_fetch:
            md = rh.get_option_market_data(
                symbol,
                expirationDate=exp,
                strikePrice=str(strike_price),
                optionType=ot,
            )
            if not md:
                continue
            # get_option_market_data returns a list of
            # [list-of-dicts] (one list per symbol).
            for entry in md:
                if not entry:
                    continue
                # entry is itself a list (one per symbol)
                items = entry if isinstance(entry, list) else [entry]
                for item in items:
                    if not item or not isinstance(item, dict):
                        continue
                    # Market data doesn't include type/strike
                    # directly — inject them.
                    item.setdefault("type", ot)
                    item.setdefault("strike_price", strike_price)
                    item.setdefault("expiration_date", exp)
                    contracts.append(self._build_contract(item, symbol, exp))

        return contracts

    def _chain_listing(
        self,
        symbol: str,
        exp: str,
        option_type: Optional[str],
    ) -> List[OptionContract]:
        """List strikes for an expiration (no greeks).

        Uses ``find_tradable_options`` which is a single paginated
        API call — fast even for large chains.  Results are filtered
        to near-the-money (±20% of current price) when possible.
        """
        options_data = rh.find_tradable_options(
            symbol,
            expirationDate=exp,
            optionType=option_type,
        )

        if not options_data:
            return []

        # Near-the-money filtering
        current_price = self._get_current_price(symbol)

        contracts: List[OptionContract] = []
        for item in options_data:
            if not item or not isinstance(item, dict):
                continue

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

    def get_option_positions(self) -> List[OptionPosition]:
        """Get all open option positions for the account.

        Calls ``rh.get_open_option_positions()`` and resolves each
        position's option instrument URL to extract the underlying
        symbol, strike, expiration, and option type.
        """
        self.client.ensure_session()

        try:
            positions_data = rh.get_open_option_positions()

            if not positions_data or positions_data == [None]:
                return []

            positions: List[OptionPosition] = []
            for item in positions_data:
                if not item or not isinstance(item, dict):
                    continue

                # Resolve the option instrument for strike/expiration/type
                option_url = item.get("option")
                symbol = item.get("chain_symbol")
                strike_price = None
                expiration_date = None
                option_type = None

                if option_url:
                    try:
                        # Extract the option ID from the URL and fetch instrument data
                        option_id = option_url.rstrip("/").split("/")[-1]
                        instrument = rh.get_option_instrument_data_by_id(option_id)
                        if instrument and isinstance(instrument, dict):
                            strike_price = instrument.get("strike_price")
                            expiration_date = instrument.get("expiration_date")
                            option_type = instrument.get("type")
                            if not symbol:
                                symbol = instrument.get("chain_symbol")
                    except Exception:
                        logger.debug(
                            "Failed to resolve option instrument: %s",
                            option_url,
                        )

                position = OptionPosition(
                    symbol=symbol,
                    expiration_date=expiration_date,
                    strike_price=strike_price,
                    option_type=option_type,
                    direction=item.get("type"),
                    quantity=item.get("quantity"),
                    average_price=item.get("average_price"),
                    created_at=item.get("created_at"),
                    updated_at=item.get("updated_at"),
                )
                positions.append(position)

            return positions
        except (RobinhoodAPIError, InvalidArgumentError, AuthRequiredError):
            raise
        except (requests.RequestException, ConnectionError, TimeoutError) as e:
            raise RobinhoodAPIError(f"Failed to fetch option positions: {e}") from e
        except Exception as e:
            raise RobinhoodAPIError(f"Failed to fetch option positions: {e}") from e
