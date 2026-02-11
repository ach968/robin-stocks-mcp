# tests/unit/test_service_portfolio.py
import pytest
from unittest.mock import MagicMock, patch
from robin_stocks_mcp.services.portfolio import PortfolioService
from robin_stocks_mcp.robinhood.client import RobinhoodClient


def test_service_initialization():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = PortfolioService(mock_client)
    assert service.client == mock_client


@patch("robin_stocks_mcp.services.portfolio.rh")
def test_get_portfolio_summary_success(mock_rh):
    mock_client = MagicMock(spec=RobinhoodClient)
    service = PortfolioService(mock_client)

    mock_rh.load_portfolio_profile.return_value = {
        "equity": "10000.50",
        "equity_previous_close": "9975.00",
    }
    mock_rh.load_account_profile.return_value = {
        "cash": "2500.00",
        "buying_power": "12500.00",
    }

    summary = service.get_portfolio_summary()

    mock_client.ensure_session.assert_called_once()
    mock_rh.load_portfolio_profile.assert_called_once()
    mock_rh.load_account_profile.assert_called_once()
    assert summary.equity == 10000.50
    assert summary.cash == 2500.00
    assert summary.buying_power == 12500.00
    assert summary.day_change == pytest.approx(25.50)
    assert summary.unrealized_pl == pytest.approx(25.50)


@patch("robin_stocks_mcp.services.portfolio.rh")
def test_get_portfolio_summary_missing_previous_close(mock_rh):
    mock_client = MagicMock(spec=RobinhoodClient)
    service = PortfolioService(mock_client)

    mock_rh.load_portfolio_profile.return_value = {
        "equity": "10000.50",
        "equity_previous_close": None,
    }
    mock_rh.load_account_profile.return_value = {
        "cash": "2500.00",
        "buying_power": "12500.00",
    }

    summary = service.get_portfolio_summary()

    assert summary.equity == 10000.50
    assert summary.day_change is None
    assert summary.unrealized_pl is None


@patch("robin_stocks_mcp.services.portfolio.rh")
def test_get_portfolio_summary_api_error(mock_rh):
    mock_client = MagicMock(spec=RobinhoodClient)
    service = PortfolioService(mock_client)

    mock_rh.load_portfolio_profile.side_effect = Exception("API Error")

    from robin_stocks_mcp.robinhood.errors import RobinhoodAPIError

    with pytest.raises(RobinhoodAPIError, match="Failed to fetch portfolio"):
        service.get_portfolio_summary()


@patch("robin_stocks_mcp.services.portfolio.rh")
def test_get_positions_success(mock_rh):
    mock_client = MagicMock(spec=RobinhoodClient)
    service = PortfolioService(mock_client)

    # Mock positions data
    mock_rh.get_open_stock_positions.return_value = [
        {
            "instrument": "https://api.robinhood.com/instruments/123/",
            "quantity": "100.0000",
            "average_buy_price": "145.00",
        },
        {
            "instrument": "https://api.robinhood.com/instruments/456/",
            "quantity": "50.0000",
            "average_buy_price": "200.00",
        },
    ]

    # Mock instrument lookup
    def mock_get_instrument(url):
        if "123" in url:
            return {"symbol": "AAPL"}
        elif "456" in url:
            return {"symbol": "GOOGL"}
        return None

    mock_rh.get_instrument_by_url.side_effect = mock_get_instrument

    # Mock quotes
    mock_rh.get_quotes.return_value = [
        {"symbol": "AAPL", "last_trade_price": "150.00"},
        {"symbol": "GOOGL", "last_trade_price": "210.00"},
    ]

    positions = service.get_positions()

    mock_client.ensure_session.assert_called_once()
    assert len(positions) == 2

    assert positions[0].symbol == "AAPL"
    assert positions[0].quantity == 100.0
    assert positions[0].average_cost == 145.00
    assert positions[0].market_value == pytest.approx(15000.00)  # 100 * 150
    assert positions[0].unrealized_pl == pytest.approx(500.00)  # 15000 - (100 * 145)

    assert positions[1].symbol == "GOOGL"
    assert positions[1].quantity == 50.0
    assert positions[1].average_cost == 200.00
    assert positions[1].market_value == pytest.approx(10500.00)  # 50 * 210
    assert positions[1].unrealized_pl == pytest.approx(500.00)  # 10500 - (50 * 200)


@patch("robin_stocks_mcp.services.portfolio.rh")
def test_get_positions_with_filter(mock_rh):
    mock_client = MagicMock(spec=RobinhoodClient)
    service = PortfolioService(mock_client)

    # Mock positions data
    mock_rh.get_open_stock_positions.return_value = [
        {
            "instrument": "https://api.robinhood.com/instruments/123/",
            "quantity": "100.0000",
            "average_buy_price": "145.00",
        },
        {
            "instrument": "https://api.robinhood.com/instruments/456/",
            "quantity": "50.0000",
            "average_buy_price": "200.00",
        },
    ]

    def mock_get_instrument(url):
        if "123" in url:
            return {"symbol": "AAPL"}
        elif "456" in url:
            return {"symbol": "GOOGL"}
        return None

    mock_rh.get_instrument_by_url.side_effect = mock_get_instrument

    # Mock quotes (only AAPL since filter excludes GOOGL)
    mock_rh.get_quotes.return_value = [
        {"symbol": "AAPL", "last_trade_price": "150.00"},
    ]

    # Filter for only AAPL
    positions = service.get_positions(symbols=["AAPL"])

    assert len(positions) == 1
    assert positions[0].symbol == "AAPL"
    assert positions[0].market_value == pytest.approx(15000.00)


@patch("robin_stocks_mcp.services.portfolio.rh")
def test_get_positions_unknown_symbol(mock_rh):
    mock_client = MagicMock(spec=RobinhoodClient)
    service = PortfolioService(mock_client)

    mock_rh.get_open_stock_positions.return_value = [
        {
            "instrument": "https://api.robinhood.com/instruments/123/",
            "quantity": "100.0000",
            "average_buy_price": "145.00",
        }
    ]

    mock_rh.get_instrument_by_url.return_value = None

    # No known symbols, so get_quotes won't be called
    mock_rh.get_quotes.return_value = []

    positions = service.get_positions()

    assert len(positions) == 1
    assert positions[0].symbol == "UNKNOWN"
    assert positions[0].market_value is None
    assert positions[0].unrealized_pl is None


@patch("robin_stocks_mcp.services.portfolio.rh")
def test_get_positions_quote_unavailable(mock_rh):
    """Positions with no matching quote should have None for computed fields."""
    mock_client = MagicMock(spec=RobinhoodClient)
    service = PortfolioService(mock_client)

    mock_rh.get_open_stock_positions.return_value = [
        {
            "instrument": "https://api.robinhood.com/instruments/123/",
            "quantity": "100.0000",
            "average_buy_price": "145.00",
        }
    ]

    mock_rh.get_instrument_by_url.return_value = {"symbol": "AAPL"}

    # Quote returns None entry (can happen with Robinhood API)
    mock_rh.get_quotes.return_value = [None]

    positions = service.get_positions()

    assert len(positions) == 1
    assert positions[0].symbol == "AAPL"
    assert positions[0].market_value is None
    assert positions[0].unrealized_pl is None


@patch("robin_stocks_mcp.services.portfolio.rh")
def test_get_positions_api_error(mock_rh):
    mock_client = MagicMock(spec=RobinhoodClient)
    service = PortfolioService(mock_client)

    mock_rh.get_open_stock_positions.side_effect = Exception("API Error")

    from robin_stocks_mcp.robinhood.errors import RobinhoodAPIError

    with pytest.raises(RobinhoodAPIError, match="Failed to fetch positions"):
        service.get_positions()
