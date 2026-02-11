import pytest
from robin_stocks_mcp.models.market import Quote, Candle
from datetime import datetime


def test_quote_creation():
    quote = Quote(
        symbol="AAPL",
        last_price=150.50,
        bid=150.45,
        ask=150.55,
        timestamp="2026-02-11T10:00:00Z"
    )
    assert quote.symbol == "AAPL"
    assert quote.last_price == 150.50


def test_candle_creation():
    candle = Candle(
        timestamp="2026-02-11T10:00:00Z",
        open=150.0,
        high=151.0,
        low=149.0,
        close=150.5,
        volume=1000000
    )
    assert candle.open == 150.0
    assert candle.volume == 1000000
