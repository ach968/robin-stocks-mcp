from unittest.mock import MagicMock, patch

import pytest

from robin_stocks_mcp.robinhood.client import RobinhoodClient
from robin_stocks_mcp.robinhood.errors import InvalidArgumentError, RobinhoodAPIError
from robin_stocks_mcp.services.orders import OrdersService


MOCK_STOCK_ORDER = {
    "id": "stock-001",
    "instrument": "https://api.robinhood.com/instruments/abc/",
    "side": "buy",
    "type": "market",
    "state": "filled",
    "quantity": "10.00000000",
    "cumulative_quantity": "10.00000000",
    "price": "150.00000000",
    "average_price": "150.25000000",
    "stop_price": None,
    "time_in_force": "gtc",
    "extended_hours": False,
    "created_at": "2026-01-15T10:30:00Z",
    "updated_at": "2026-01-15T10:30:05Z",
    "last_transaction_at": "2026-01-15T10:30:05Z",
    "executions": [
        {
            "price": "150.25000000",
            "quantity": "10.00000000",
            "settlement_date": "2026-01-17",
            "timestamp": "2026-01-15T10:30:03Z",
            "id": "exec-001",
        }
    ],
}

MOCK_OPTION_ORDER = {
    "id": "option-001",
    "chain_symbol": "AAPL",
    "direction": "debit",
    "type": "limit",
    "state": "filled",
    "quantity": "1.00000000",
    "pending_quantity": "0.00000000",
    "processed_quantity": "1.00000000",
    "price": "3.50000000",
    "premium": "350.00000000",
    "processed_premium": "350.00000000",
    "opening_strategy": "long_call",
    "closing_strategy": None,
    "legs": [{"side": "buy", "option": "https://api.robinhood.com/options/abc/"}],
    "created_at": "2026-01-15T11:00:00Z",
    "updated_at": "2026-01-15T11:00:03Z",
    "time_in_force": "gtc",
}

MOCK_CRYPTO_ORDER = {
    "id": "crypto-001",
    "currency_pair_id": "btc-usd",
    "side": "buy",
    "type": "market",
    "state": "filled",
    "quantity": "0.01000000",
    "cumulative_quantity": "0.01000000",
    "price": "40000.00000000",
    "average_price": "40000.00000000",
    "executions": [],
    "created_at": "2026-01-15T12:00:00Z",
    "updated_at": "2026-01-15T12:00:02Z",
    "time_in_force": "gtc",
}


def _make_service():
    client = MagicMock(spec=RobinhoodClient)
    return OrdersService(client), client


class TestInit:
    def test_service_initialization(self):
        service, client = _make_service()
        assert service.client == client


class TestGetOrderHistory:
    def test_calls_ensure_session(self):
        service, client = _make_service()
        with patch("robin_stocks_mcp.services.orders.rh") as mock_rh:
            mock_rh.get_all_stock_orders.return_value = []
            mock_rh.get_all_option_orders.return_value = []
            mock_rh.get_all_crypto_orders.return_value = []
            service.get_order_history()
            client.ensure_session.assert_called_once()

    def test_invalid_order_type_raises(self):
        service, _ = _make_service()
        with pytest.raises(InvalidArgumentError, match="Invalid order type"):
            service.get_order_history(order_type="invalid")

    def test_all_types_returned(self):
        service, _ = _make_service()
        with patch("robin_stocks_mcp.services.orders.rh") as mock_rh:
            mock_rh.get_all_stock_orders.return_value = [MOCK_STOCK_ORDER]
            mock_rh.get_all_option_orders.return_value = [MOCK_OPTION_ORDER]
            mock_rh.get_all_crypto_orders.return_value = [MOCK_CRYPTO_ORDER]
            mock_rh.get_instrument_by_url.return_value = {"symbol": "AAPL"}

            history = service.get_order_history()

            assert len(history.stock_orders) == 1
            assert len(history.option_orders) == 1
            assert len(history.crypto_orders) == 1

    def test_stock_only(self):
        service, _ = _make_service()
        with patch("robin_stocks_mcp.services.orders.rh") as mock_rh:
            mock_rh.get_all_stock_orders.return_value = [MOCK_STOCK_ORDER]
            mock_rh.get_instrument_by_url.return_value = {"symbol": "AAPL"}

            history = service.get_order_history(order_type="stock")

            assert len(history.stock_orders) == 1
            assert history.option_orders == []
            assert history.crypto_orders == []
            mock_rh.get_all_option_orders.assert_not_called()
            mock_rh.get_all_crypto_orders.assert_not_called()

    def test_option_only(self):
        service, _ = _make_service()
        with patch("robin_stocks_mcp.services.orders.rh") as mock_rh:
            mock_rh.get_all_option_orders.return_value = [MOCK_OPTION_ORDER]

            history = service.get_order_history(order_type="option")

            assert history.stock_orders == []
            assert len(history.option_orders) == 1
            assert history.crypto_orders == []

    def test_crypto_only(self):
        service, _ = _make_service()
        with patch("robin_stocks_mcp.services.orders.rh") as mock_rh:
            mock_rh.get_all_crypto_orders.return_value = [MOCK_CRYPTO_ORDER]

            history = service.get_order_history(order_type="crypto")

            assert history.stock_orders == []
            assert history.option_orders == []
            assert len(history.crypto_orders) == 1

    def test_none_defaults_to_all(self):
        service, _ = _make_service()
        with patch("robin_stocks_mcp.services.orders.rh") as mock_rh:
            mock_rh.get_all_stock_orders.return_value = []
            mock_rh.get_all_option_orders.return_value = []
            mock_rh.get_all_crypto_orders.return_value = []

            service.get_order_history(order_type=None)

            mock_rh.get_all_stock_orders.assert_called_once()
            mock_rh.get_all_option_orders.assert_called_once()
            mock_rh.get_all_crypto_orders.assert_called_once()


class TestStockOrders:
    def test_symbol_filter(self):
        service, _ = _make_service()
        with patch("robin_stocks_mcp.services.orders.rh") as mock_rh:
            mock_rh.get_all_stock_orders.return_value = [MOCK_STOCK_ORDER]
            mock_rh.get_instrument_by_url.return_value = {"symbol": "AAPL"}

            history = service.get_order_history(order_type="stock", symbol="MSFT")

            assert len(history.stock_orders) == 0

    def test_symbol_filter_matches(self):
        service, _ = _make_service()
        with patch("robin_stocks_mcp.services.orders.rh") as mock_rh:
            mock_rh.get_all_stock_orders.return_value = [MOCK_STOCK_ORDER]
            mock_rh.get_instrument_by_url.return_value = {"symbol": "AAPL"}

            history = service.get_order_history(order_type="stock", symbol="AAPL")

            assert len(history.stock_orders) == 1
            assert history.stock_orders[0].symbol == "AAPL"

    def test_start_date_passed_through(self):
        service, _ = _make_service()
        with patch("robin_stocks_mcp.services.orders.rh") as mock_rh:
            mock_rh.get_all_stock_orders.return_value = []

            service.get_order_history(order_type="stock", start_date="2026-01-01")

            mock_rh.get_all_stock_orders.assert_called_once_with(
                start_date="2026-01-01"
            )

    def test_execution_parsing(self):
        service, _ = _make_service()
        with patch("robin_stocks_mcp.services.orders.rh") as mock_rh:
            mock_rh.get_all_stock_orders.return_value = [MOCK_STOCK_ORDER]
            mock_rh.get_instrument_by_url.return_value = {"symbol": "AAPL"}

            history = service.get_order_history(order_type="stock")

            order = history.stock_orders[0]
            assert len(order.executions) == 1
            assert order.executions[0].price == 150.25
            assert order.executions[0].quantity == 10.0

    def test_skips_none_items(self):
        service, _ = _make_service()
        with patch("robin_stocks_mcp.services.orders.rh") as mock_rh:
            mock_rh.get_all_stock_orders.return_value = [None, MOCK_STOCK_ORDER, None]
            mock_rh.get_instrument_by_url.return_value = {"symbol": "AAPL"}

            history = service.get_order_history(order_type="stock")

            assert len(history.stock_orders) == 1

    def test_empty_response(self):
        service, _ = _make_service()
        with patch("robin_stocks_mcp.services.orders.rh") as mock_rh:
            mock_rh.get_all_stock_orders.return_value = None

            history = service.get_order_history(order_type="stock")

            assert history.stock_orders == []


class TestOptionOrders:
    def test_symbol_filter(self):
        service, _ = _make_service()
        with patch("robin_stocks_mcp.services.orders.rh") as mock_rh:
            mock_rh.get_all_option_orders.return_value = [MOCK_OPTION_ORDER]

            history = service.get_order_history(order_type="option", symbol="MSFT")

            assert len(history.option_orders) == 0

    def test_symbol_filter_matches(self):
        service, _ = _make_service()
        with patch("robin_stocks_mcp.services.orders.rh") as mock_rh:
            mock_rh.get_all_option_orders.return_value = [MOCK_OPTION_ORDER]

            history = service.get_order_history(order_type="option", symbol="AAPL")

            assert len(history.option_orders) == 1
            assert history.option_orders[0].chain_symbol == "AAPL"

    def test_start_date_passed_through(self):
        service, _ = _make_service()
        with patch("robin_stocks_mcp.services.orders.rh") as mock_rh:
            mock_rh.get_all_option_orders.return_value = []

            service.get_order_history(order_type="option", start_date="2026-01-01")

            mock_rh.get_all_option_orders.assert_called_once_with(
                start_date="2026-01-01"
            )


class TestCryptoOrders:
    def test_start_date_not_passed(self):
        service, _ = _make_service()
        with patch("robin_stocks_mcp.services.orders.rh") as mock_rh:
            mock_rh.get_all_crypto_orders.return_value = []

            service.get_order_history(order_type="crypto", start_date="2026-01-01")

            mock_rh.get_all_crypto_orders.assert_called_once_with()


class TestErrorHandling:
    def test_api_error_wrapped(self):
        service, _ = _make_service()
        with patch("robin_stocks_mcp.services.orders.rh") as mock_rh:
            mock_rh.get_all_stock_orders.side_effect = Exception("API Error")

            with pytest.raises(
                RobinhoodAPIError, match="Failed to fetch order history"
            ):
                service.get_order_history(order_type="stock")
