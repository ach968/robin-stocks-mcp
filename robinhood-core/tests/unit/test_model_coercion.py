from robinhood_core.models.market import Quote, Candle
from robinhood_core.models.base import coerce_numeric, coerce_timestamp, coerce_int


def test_coerce_numeric_with_string():
    assert coerce_numeric("150.50") == 150.50


def test_coerce_numeric_with_float():
    assert coerce_numeric(150.50) == 150.50


def test_coerce_numeric_with_none():
    assert coerce_numeric(None) is None


def test_coerce_numeric_with_invalid():
    assert coerce_numeric("invalid") is None


def test_coerce_int_with_string():
    assert coerce_int("100") == 100


def test_coerce_int_with_float():
    assert coerce_int(100.5) == 100


def test_coerce_timestamp_with_iso():
    result = coerce_timestamp("2026-02-11T10:00:00Z")
    assert "2026-02-11" in result


def test_quote_accepts_string_prices():
    quote = Quote(
        symbol="AAPL",
        last_price="150.50",
        bid="150.45",
        ask="150.55",
        timestamp="2026-02-11T10:00:00Z",
    )
    assert quote.last_price == 150.50
    assert isinstance(quote.last_price, float)


def test_candle_accepts_string_values():
    candle = Candle(
        timestamp="2026-02-11T10:00:00Z",
        open="150.0",
        high="151.0",
        low="149.0",
        close="150.5",
        volume="1000000",
    )
    assert candle.volume == 1000000
    assert isinstance(candle.volume, int)
    assert candle.open == 150.0
    assert candle.close == 150.5


def test_quote_accepts_none_values():
    quote = Quote(
        symbol="AAPL",
        last_price="150.50",
        bid=None,
        ask=None,
        timestamp="2026-02-11T10:00:00Z",
    )
    assert quote.bid is None
    assert quote.ask is None
    assert quote.last_price == 150.50


def test_coerce_numeric_with_empty_string():
    assert coerce_numeric("") is None


def test_coerce_int_with_none():
    assert coerce_int(None) is None


def test_coerce_timestamp_with_none():
    assert coerce_timestamp(None) is None


def test_coerce_timestamp_with_invalid_string():
    result = coerce_timestamp("invalid")
    assert result == "invalid"


def test_quote_accepts_integer_prices():
    quote = Quote(symbol="AAPL", last_price=150, timestamp="2026-02-11T10:00:00Z")
    assert quote.last_price == 150.0
    assert isinstance(quote.last_price, float)
