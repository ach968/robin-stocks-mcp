from unittest.mock import MagicMock, patch
from robin_stocks_mcp.services.market_data import MarketDataService
from robin_stocks_mcp.robinhood.client import RobinhoodClient


def test_market_service_with_mocked_data():
    mock_client = MagicMock(spec=RobinhoodClient)
    mock_client.ensure_session = MagicMock()

    service = MarketDataService(mock_client)

    # Mock robin_stocks
    with patch("robin_stocks_mcp.services.market_data.rh") as mock_rh:
        mock_rh.get_quotes.return_value = [
            {
                "symbol": "AAPL",
                "last_trade_price": "150.50",
                "bid_price": "150.45",
                "ask_price": "150.55",
                "updated_at": "2026-02-11T10:00:00Z",
            }
        ]

        quotes = service.get_current_price(["AAPL"])

        assert len(quotes) == 1
        assert quotes[0].symbol == "AAPL"
        assert quotes[0].last_price == 150.50
        mock_client.ensure_session.assert_called_once()


def test_market_service_get_price_history_mocked():
    mock_client = MagicMock(spec=RobinhoodClient)
    mock_client.ensure_session = MagicMock()

    service = MarketDataService(mock_client)

    with patch("robin_stocks_mcp.services.market_data.rh") as mock_rh:
        mock_rh.get_stock_historicals.return_value = [
            {
                "begins_at": "2026-02-11T10:00:00Z",
                "open_price": "150.0",
                "high_price": "155.0",
                "low_price": "149.0",
                "close_price": "152.0",
                "volume": "1000000",
            }
        ]

        candles = service.get_price_history("AAPL", interval="day", span="year")

        assert len(candles) == 1
        assert candles[0].open == 150.0
        assert candles[0].high == 155.0
        assert candles[0].low == 149.0
        assert candles[0].close == 152.0
        assert candles[0].volume == 1000000
        mock_rh.get_stock_historicals.assert_called_once_with(
            "AAPL", interval="day", span="year", bounds="regular"
        )


def test_market_service_with_multiple_quotes():
    mock_client = MagicMock(spec=RobinhoodClient)
    mock_client.ensure_session = MagicMock()

    service = MarketDataService(mock_client)

    with patch("robin_stocks_mcp.services.market_data.rh") as mock_rh:
        mock_rh.get_quotes.return_value = [
            {
                "symbol": "AAPL",
                "last_trade_price": "150.50",
                "bid_price": "150.45",
                "ask_price": "150.55",
                "updated_at": "2026-02-11T10:00:00Z",
                "previous_close": "149.00",
            },
            {
                "symbol": "GOOGL",
                "last_trade_price": "2800.00",
                "bid_price": "2799.00",
                "ask_price": "2801.00",
                "updated_at": "2026-02-11T10:00:00Z",
            },
        ]

        quotes = service.get_current_price(["AAPL", "GOOGL"])

        assert len(quotes) == 2
        assert quotes[0].symbol == "AAPL"
        assert quotes[0].last_price == 150.50
        assert quotes[0].previous_close == 149.00
        # change_percent is now computed: ((150.50 - 149.00) / 149.00) * 100
        import pytest

        expected_change = ((150.50 - 149.00) / 149.00) * 100
        assert quotes[0].change_percent == pytest.approx(expected_change)
        assert quotes[1].symbol == "GOOGL"
        assert quotes[1].last_price == 2800.00
        assert quotes[1].change_percent is None  # no previous_close provided


def test_market_service_with_single_symbol():
    mock_client = MagicMock(spec=RobinhoodClient)
    mock_client.ensure_session = MagicMock()

    service = MarketDataService(mock_client)

    with patch("robin_stocks_mcp.services.market_data.rh") as mock_rh:
        mock_rh.get_quotes.return_value = {
            "symbol": "MSFT",
            "last_trade_price": "300.00",
            "bid_price": "299.00",
            "ask_price": "301.00",
            "updated_at": "2026-02-11T10:00:00Z",
        }

        quotes = service.get_current_price(["MSFT"])

        assert len(quotes) == 1
        assert quotes[0].symbol == "MSFT"
        assert quotes[0].last_price == 300.00


def test_market_service_with_empty_response():
    mock_client = MagicMock(spec=RobinhoodClient)
    mock_client.ensure_session = MagicMock()

    service = MarketDataService(mock_client)

    with patch("robin_stocks_mcp.services.market_data.rh") as mock_rh:
        mock_rh.get_quotes.return_value = []

        quotes = service.get_current_price(["UNKNOWN"])

        assert len(quotes) == 0
        assert quotes == []


def test_market_service_price_history_empty_response():
    mock_client = MagicMock(spec=RobinhoodClient)
    mock_client.ensure_session = MagicMock()

    service = MarketDataService(mock_client)

    with patch("robin_stocks_mcp.services.market_data.rh") as mock_rh:
        mock_rh.get_stock_historicals.return_value = []

        candles = service.get_price_history("AAPL")

        assert len(candles) == 0
        assert candles == []


def test_market_service_with_string_numeric_coercion():
    """Test that string values from robin_stocks are properly coerced to numeric types"""
    mock_client = MagicMock(spec=RobinhoodClient)
    mock_client.ensure_session = MagicMock()

    service = MarketDataService(mock_client)

    with patch("robin_stocks_mcp.services.market_data.rh") as mock_rh:
        # Simulate robin_stocks returning string values
        mock_rh.get_quotes.return_value = [
            {
                "symbol": "TSLA",
                "last_trade_price": "250.5000",
                "bid_price": "250.0000",
                "ask_price": "251.0000",
                "updated_at": "2026-02-11T10:00:00Z",
            }
        ]

        quotes = service.get_current_price(["TSLA"])

        assert len(quotes) == 1
        assert quotes[0].symbol == "TSLA"
        # Verify coercion happened
        assert quotes[0].last_price == 250.5
        assert isinstance(quotes[0].last_price, float)
        assert quotes[0].bid == 250.0
        assert quotes[0].ask == 251.0
