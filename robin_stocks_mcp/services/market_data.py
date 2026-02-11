from typing import List
import requests
import robin_stocks.robinhood as rh
from robin_stocks_mcp.models import Quote, Candle
from robin_stocks_mcp.robinhood.client import RobinhoodClient
from robin_stocks_mcp.robinhood.errors import (
    AuthRequiredError,
    InvalidArgumentError,
    RobinhoodAPIError,
)


class MarketDataService:
    """Service for market data operations."""

    def __init__(self, client: RobinhoodClient):
        self.client = client

    def get_current_price(self, symbols: List[str]) -> List[Quote]:
        """Get current price quotes for symbols."""
        if not symbols:
            raise InvalidArgumentError("At least one symbol is required")

        self.client.ensure_session()

        try:
            # Handle single symbol vs list
            if len(symbols) == 1:
                data = rh.get_quotes(symbols[0])
            else:
                data = rh.get_quotes(symbols)

            if not data:
                return []

            # Ensure list format
            if not isinstance(data, list):
                data = [data]

            quotes = []
            for item in data:
                # Compute change_percent from last_trade_price and previous_close
                # since robin_stocks API does not return change_percent directly.
                last_trade_price = item.get("last_trade_price")
                previous_close = item.get("previous_close")
                change_percent = None
                if last_trade_price is not None and previous_close is not None:
                    try:
                        ltp = float(last_trade_price)
                        pc = float(previous_close)
                        if pc != 0:
                            change_percent = ((ltp - pc) / pc) * 100
                    except (ValueError, TypeError):
                        change_percent = None

                quote = Quote(
                    symbol=item.get("symbol", ""),
                    last_price=last_trade_price,
                    bid=item.get("bid_price"),
                    ask=item.get("ask_price"),
                    timestamp=item.get("updated_at"),
                    previous_close=previous_close,
                    change_percent=change_percent,
                )
                quotes.append(quote)

            return quotes
        except (RobinhoodAPIError, InvalidArgumentError, AuthRequiredError):
            raise
        except (requests.RequestException, ConnectionError, TimeoutError) as e:
            raise RobinhoodAPIError(f"Failed to fetch quotes: {e}") from e
        except Exception as e:
            raise RobinhoodAPIError(f"Failed to fetch quotes: {e}") from e

    def get_price_history(
        self,
        symbol: str,
        interval: str = "hour",
        span: str = "week",
        bounds: str = "regular",
    ) -> List[Candle]:
        """Get historical price data for a symbol."""
        if not symbol:
            raise InvalidArgumentError("Symbol is required")

        # Validate inputs
        valid_intervals = ["5minute", "10minute", "hour", "day", "week"]
        valid_spans = ["day", "week", "month", "3month", "year", "5year"]
        valid_bounds = ["extended", "trading", "regular"]

        if interval not in valid_intervals:
            raise InvalidArgumentError(
                f"Invalid interval. Must be one of: {valid_intervals}"
            )
        if span not in valid_spans:
            raise InvalidArgumentError(f"Invalid span. Must be one of: {valid_spans}")
        if bounds not in valid_bounds:
            raise InvalidArgumentError(
                f"Invalid bounds. Must be one of: {valid_bounds}"
            )

        self.client.ensure_session()

        try:
            data = rh.get_stock_historicals(
                symbol, interval=interval, span=span, bounds=bounds
            )

            if not data:
                return []

            candles = []
            for item in data:
                candle = Candle(
                    timestamp=item.get("begins_at"),
                    open=item.get("open_price"),
                    high=item.get("high_price"),
                    low=item.get("low_price"),
                    close=item.get("close_price"),
                    volume=item.get("volume"),
                )
                candles.append(candle)

            return candles
        except (RobinhoodAPIError, InvalidArgumentError, AuthRequiredError):
            raise
        except (requests.RequestException, ConnectionError, TimeoutError) as e:
            raise RobinhoodAPIError(f"Failed to fetch price history: {e}") from e
        except Exception as e:
            raise RobinhoodAPIError(f"Failed to fetch price history: {e}") from e
