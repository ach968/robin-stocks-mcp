import pytest

from robin_stocks_mcp.models.orders import (
    CryptoOrder,
    OptionOrder,
    OrderExecution,
    OrderHistory,
    StockOrder,
)


class TestOrderExecution:
    def test_coerces_string_numerics(self):
        ex = OrderExecution(price="10.50", quantity="100")
        assert ex.price == 10.50
        assert ex.quantity == 100.0

    def test_none_values(self):
        ex = OrderExecution()
        assert ex.price is None
        assert ex.quantity is None
        assert ex.timestamp is None

    def test_timestamp_normalization(self):
        ex = OrderExecution(timestamp="2026-01-15T10:30:00Z")
        assert ex.timestamp == "2026-01-15T10:30:00Z"

    def test_invalid_numeric_becomes_none(self):
        ex = OrderExecution(price="not_a_number")
        assert ex.price is None


class TestStockOrder:
    def test_full_construction(self):
        order = StockOrder(
            id="order-123",
            symbol="AAPL",
            side="buy",
            type="market",
            state="filled",
            quantity="10",
            cumulative_quantity="10",
            price="150.00",
            average_price="150.25",
            time_in_force="gtc",
        )
        assert order.symbol == "AAPL"
        assert order.quantity == 10.0
        assert order.price == 150.0
        assert order.average_price == 150.25

    def test_executions_list(self):
        order = StockOrder(
            executions=[
                OrderExecution(price="150.00", quantity="5"),
                OrderExecution(price="150.50", quantity="5"),
            ]
        )
        assert len(order.executions) == 2
        assert order.executions[0].price == 150.0

    def test_timestamp_coercion(self):
        order = StockOrder(created_at="2026-01-15T10:30:00Z")
        assert order.created_at == "2026-01-15T10:30:00Z"

    def test_defaults_to_empty_executions(self):
        order = StockOrder()
        assert order.executions == []


class TestOptionOrder:
    def test_full_construction(self):
        order = OptionOrder(
            id="opt-456",
            chain_symbol="SPY",
            direction="debit",
            type="limit",
            state="filled",
            quantity="1",
            price="3.50",
            premium="350.00",
        )
        assert order.chain_symbol == "SPY"
        assert order.quantity == 1.0
        assert order.premium == 350.0

    def test_string_numeric_coercion(self):
        order = OptionOrder(
            pending_quantity="0",
            processed_quantity="5",
            processed_premium="500.00",
        )
        assert order.pending_quantity == 0.0
        assert order.processed_quantity == 5.0
        assert order.processed_premium == 500.0


class TestCryptoOrder:
    def test_full_construction(self):
        order = CryptoOrder(
            id="crypto-789",
            side="buy",
            state="filled",
            quantity="0.5",
            price="40000.00",
            average_price="40000.00",
        )
        assert order.quantity == 0.5
        assert order.price == 40000.0


class TestOrderHistory:
    def test_empty_defaults(self):
        history = OrderHistory()
        assert history.stock_orders == []
        assert history.option_orders == []
        assert history.crypto_orders == []

    def test_model_dump_structure(self):
        history = OrderHistory(
            stock_orders=[StockOrder(id="s1", symbol="AAPL")],
            option_orders=[OptionOrder(id="o1", chain_symbol="SPY")],
            crypto_orders=[CryptoOrder(id="c1", side="buy")],
        )
        dumped = history.model_dump()
        assert len(dumped["stock_orders"]) == 1
        assert len(dumped["option_orders"]) == 1
        assert len(dumped["crypto_orders"]) == 1
        assert dumped["stock_orders"][0]["symbol"] == "AAPL"
