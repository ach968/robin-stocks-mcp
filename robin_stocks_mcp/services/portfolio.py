# robin_stocks_mcp/services/portfolio.py
from typing import List, Optional
import requests
import robin_stocks.robinhood as rh
from robin_stocks_mcp.models import PortfolioSummary, Position
from robin_stocks_mcp.robinhood.client import RobinhoodClient
from robin_stocks_mcp.robinhood.errors import (
    AuthRequiredError,
    InvalidArgumentError,
    RobinhoodAPIError,
)


class PortfolioService:
    """Service for portfolio operations."""

    def __init__(self, client: RobinhoodClient):
        self.client = client

    def get_portfolio_summary(self) -> PortfolioSummary:
        """Get portfolio summary."""
        self.client.ensure_session()

        try:
            portfolio = rh.load_portfolio_profile()
            account = rh.load_account_profile()

            equity = portfolio.get("equity")
            equity_previous_close = portfolio.get("equity_previous_close")

            day_change = None
            if equity is not None and equity_previous_close is not None:
                try:
                    day_change = float(equity) - float(equity_previous_close)
                except (ValueError, TypeError):
                    day_change = None

            return PortfolioSummary(
                equity=equity,
                cash=account.get("cash"),
                buying_power=account.get("buying_power"),
                day_change=day_change,
                unrealized_pl=day_change,
            )
        except (RobinhoodAPIError, InvalidArgumentError, AuthRequiredError):
            raise
        except (requests.RequestException, ConnectionError, TimeoutError) as e:
            raise RobinhoodAPIError(f"Failed to fetch portfolio: {e}") from e
        except Exception as e:
            raise RobinhoodAPIError(f"Failed to fetch portfolio: {e}") from e

    def get_positions(self, symbols: Optional[List[str]] = None) -> List[Position]:
        """Get portfolio positions, optionally filtered by symbols."""
        self.client.ensure_session()

        try:
            positions_data = rh.get_open_stock_positions()

            # First pass: resolve symbols from instrument URLs
            resolved = []
            for item in positions_data:
                instrument = rh.get_instrument_by_url(item.get("instrument"))
                symbol = instrument.get("symbol") if instrument else None

                if symbols and symbol not in symbols:
                    continue

                resolved.append((symbol or "UNKNOWN", item))

            # Batch-fetch current quotes for all position symbols
            known_symbols = [s for s, _ in resolved if s != "UNKNOWN"]
            quotes_map: dict = {}
            if known_symbols:
                quotes = rh.get_quotes(known_symbols)
                if quotes:
                    for q in quotes:
                        if q and q.get("symbol"):
                            quotes_map[q["symbol"]] = q

            # Build position objects with computed market_value / unrealized_pl
            positions = []
            for symbol, item in resolved:
                quantity = item.get("quantity")
                avg_buy_price = item.get("average_buy_price")

                market_value = None
                unrealized_pl = None

                quote = quotes_map.get(symbol)
                if quote and quantity is not None:
                    try:
                        current_price = float(quote.get("last_trade_price", 0))
                        qty = float(quantity)
                        market_value = qty * current_price

                        if avg_buy_price is not None:
                            cost_basis = qty * float(avg_buy_price)
                            unrealized_pl = market_value - cost_basis
                    except (ValueError, TypeError):
                        pass

                position = Position(
                    symbol=symbol,
                    quantity=quantity,
                    average_cost=avg_buy_price,
                    market_value=market_value,
                    unrealized_pl=unrealized_pl,
                )
                positions.append(position)

            return positions
        except (RobinhoodAPIError, InvalidArgumentError, AuthRequiredError):
            raise
        except (requests.RequestException, ConnectionError, TimeoutError) as e:
            raise RobinhoodAPIError(f"Failed to fetch positions: {e}") from e
        except Exception as e:
            raise RobinhoodAPIError(f"Failed to fetch positions: {e}") from e
