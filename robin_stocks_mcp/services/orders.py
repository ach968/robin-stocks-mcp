import logging
from typing import List, Optional

import requests
import robin_stocks.robinhood as rh

from robin_stocks_mcp.models.orders import (
    CryptoOrder,
    OptionOrder,
    OrderExecution,
    OrderHistory,
    StockOrder,
)
from robin_stocks_mcp.robinhood.client import RobinhoodClient
from robin_stocks_mcp.robinhood.errors import (
    AuthRequiredError,
    InvalidArgumentError,
    RobinhoodAPIError,
)

logger = logging.getLogger(__name__)


class OrdersService:
    def __init__(self, client: RobinhoodClient):
        self.client = client

    def get_order_history(
        self,
        order_type: Optional[str] = None,
        symbol: Optional[str] = None,
        start_date: Optional[str] = None,
    ) -> OrderHistory:
        self.client.ensure_session()

        order_type = (order_type or "all").lower()
        valid_types = {"all", "stock", "option", "crypto"}
        if order_type not in valid_types:
            raise InvalidArgumentError(
                f"Invalid order type '{order_type}'. Must be one of: {', '.join(sorted(valid_types))}"
            )

        try:
            stock_orders: List[StockOrder] = []
            option_orders: List[OptionOrder] = []
            crypto_orders: List[CryptoOrder] = []

            if order_type in ("all", "stock"):
                stock_orders = self._get_stock_orders(symbol, start_date)

            if order_type in ("all", "option"):
                option_orders = self._get_option_orders(symbol, start_date)

            if order_type in ("all", "crypto"):
                crypto_orders = self._get_crypto_orders(start_date)

            return OrderHistory(
                stock_orders=stock_orders,
                option_orders=option_orders,
                crypto_orders=crypto_orders,
            )
        except (RobinhoodAPIError, InvalidArgumentError, AuthRequiredError):
            raise
        except (requests.RequestException, ConnectionError, TimeoutError) as e:
            raise RobinhoodAPIError(f"Failed to fetch order history: {e}") from e
        except Exception as e:
            raise RobinhoodAPIError(f"Failed to fetch order history: {e}") from e

    def _get_stock_orders(
        self,
        symbol: Optional[str],
        start_date: Optional[str],
    ) -> List[StockOrder]:
        raw = rh.get_all_stock_orders(start_date=start_date)
        if not raw:
            return []

        orders: List[StockOrder] = []
        for item in raw:
            if not item or not isinstance(item, dict):
                continue

            order_symbol = self._resolve_stock_symbol(item)

            if symbol and order_symbol and order_symbol.upper() != symbol.upper():
                continue

            executions = [
                OrderExecution(
                    price=ex.get("price"),
                    quantity=ex.get("quantity"),
                    settlement_date=ex.get("settlement_date"),
                    timestamp=ex.get("timestamp"),
                    id=ex.get("id"),
                )
                for ex in (item.get("executions") or [])
                if ex and isinstance(ex, dict)
            ]

            orders.append(
                StockOrder(
                    id=item.get("id"),
                    symbol=order_symbol,
                    side=item.get("side"),
                    type=item.get("type"),
                    state=item.get("state"),
                    quantity=item.get("quantity"),
                    cumulative_quantity=item.get("cumulative_quantity"),
                    price=item.get("price"),
                    average_price=item.get("average_price"),
                    stop_price=item.get("stop_price"),
                    executions=executions,
                    created_at=item.get("created_at"),
                    updated_at=item.get("updated_at"),
                    last_transaction_at=item.get("last_transaction_at"),
                    time_in_force=item.get("time_in_force"),
                    extended_hours=item.get("extended_hours"),
                )
            )

        return orders

    def _get_option_orders(
        self,
        symbol: Optional[str],
        start_date: Optional[str],
    ) -> List[OptionOrder]:
        raw = rh.get_all_option_orders(start_date=start_date)
        if not raw:
            return []

        orders: List[OptionOrder] = []
        for item in raw:
            if not item or not isinstance(item, dict):
                continue

            chain_symbol = item.get("chain_symbol")
            if symbol and chain_symbol and chain_symbol.upper() != symbol.upper():
                continue

            orders.append(
                OptionOrder(
                    id=item.get("id"),
                    chain_symbol=chain_symbol,
                    direction=item.get("direction"),
                    type=item.get("type"),
                    state=item.get("state"),
                    quantity=item.get("quantity"),
                    pending_quantity=item.get("pending_quantity"),
                    processed_quantity=item.get("processed_quantity"),
                    price=item.get("price"),
                    premium=item.get("premium"),
                    processed_premium=item.get("processed_premium"),
                    opening_strategy=item.get("opening_strategy"),
                    closing_strategy=item.get("closing_strategy"),
                    legs=item.get("legs"),
                    created_at=item.get("created_at"),
                    updated_at=item.get("updated_at"),
                    time_in_force=item.get("time_in_force"),
                )
            )

        return orders

    def _get_crypto_orders(
        self,
        start_date: Optional[str],
    ) -> List[CryptoOrder]:
        # robin-stocks crypto orders API does not support start_date
        raw = rh.get_all_crypto_orders()
        if not raw:
            return []

        orders: List[CryptoOrder] = []
        for item in raw:
            if not item or not isinstance(item, dict):
                continue

            orders.append(
                CryptoOrder(
                    id=item.get("id"),
                    currency_pair_id=item.get("currency_pair_id"),
                    side=item.get("side"),
                    type=item.get("type"),
                    state=item.get("state"),
                    quantity=item.get("quantity"),
                    cumulative_quantity=item.get("cumulative_quantity"),
                    price=item.get("price"),
                    average_price=item.get("average_price"),
                    executions=item.get("executions"),
                    created_at=item.get("created_at"),
                    updated_at=item.get("updated_at"),
                    time_in_force=item.get("time_in_force"),
                )
            )

        return orders

    @staticmethod
    def _resolve_stock_symbol(item: dict) -> Optional[str]:
        instrument_url = item.get("instrument")
        if not instrument_url:
            return None
        try:
            instrument = rh.get_instrument_by_url(instrument_url)
            if instrument and isinstance(instrument, dict):
                return instrument.get("symbol")
        except Exception:
            logger.debug("Failed to resolve instrument: %s", instrument_url)
        return None
