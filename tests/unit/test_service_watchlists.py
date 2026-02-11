# tests/unit/test_service_watchlists.py
from unittest.mock import MagicMock, patch, call
from robin_stocks_mcp.services.watchlists import WatchlistsService
from robin_stocks_mcp.robinhood.client import RobinhoodClient
from robin_stocks_mcp.robinhood.errors import RobinhoodAPIError
import pytest


def test_service_initialization():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = WatchlistsService(mock_client)
    assert service.client == mock_client


def test_get_watchlists_parses_results_dict():
    """get_all_watchlists returns a dict with a 'results' key."""
    mock_client = MagicMock(spec=RobinhoodClient)
    service = WatchlistsService(mock_client)

    with patch("robin_stocks_mcp.services.watchlists.rh") as mock_rh:
        mock_rh.get_all_watchlists.return_value = {
            "results": [
                {"id": "abc-123", "display_name": "My First List"},
                {"id": "def-456", "display_name": "Tech Stocks"},
            ]
        }
        # get_watchlist_by_name returns instrument entries
        mock_rh.get_watchlist_by_name.side_effect = [
            [{"instrument": "https://api.robinhood.com/instruments/inst1/"}],
            [
                {"instrument": "https://api.robinhood.com/instruments/inst2/"},
                {"instrument": "https://api.robinhood.com/instruments/inst3/"},
            ],
        ]
        mock_rh.get_symbol_by_url.side_effect = ["AAPL", "GOOGL", "MSFT"]

        watchlists = service.get_watchlists()

        assert len(watchlists) == 2

        assert watchlists[0].id == "abc-123"
        assert watchlists[0].name == "My First List"
        assert watchlists[0].symbols == ["AAPL"]

        assert watchlists[1].id == "def-456"
        assert watchlists[1].name == "Tech Stocks"
        assert watchlists[1].symbols == ["GOOGL", "MSFT"]

        mock_client.ensure_session.assert_called_once()
        mock_rh.get_watchlist_by_name.assert_any_call(name="My First List")
        mock_rh.get_watchlist_by_name.assert_any_call(name="Tech Stocks")


def test_get_watchlists_empty_results():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = WatchlistsService(mock_client)

    with patch("robin_stocks_mcp.services.watchlists.rh") as mock_rh:
        mock_rh.get_all_watchlists.return_value = {"results": []}

        watchlists = service.get_watchlists()

        assert watchlists == []


def test_get_watchlists_none_response():
    """Handle case where get_all_watchlists returns None."""
    mock_client = MagicMock(spec=RobinhoodClient)
    service = WatchlistsService(mock_client)

    with patch("robin_stocks_mcp.services.watchlists.rh") as mock_rh:
        mock_rh.get_all_watchlists.return_value = None

        watchlists = service.get_watchlists()

        assert watchlists == []


def test_get_watchlists_symbol_resolution_failure_returns_empty_symbols():
    """If symbol resolution fails for a watchlist, return empty symbols list."""
    mock_client = MagicMock(spec=RobinhoodClient)
    service = WatchlistsService(mock_client)

    with patch("robin_stocks_mcp.services.watchlists.rh") as mock_rh:
        mock_rh.get_all_watchlists.return_value = {
            "results": [
                {"id": "abc-123", "display_name": "My List"},
            ]
        }
        mock_rh.get_watchlist_by_name.side_effect = Exception("API error")

        watchlists = service.get_watchlists()

        assert len(watchlists) == 1
        assert watchlists[0].symbols == []


def test_get_watchlists_api_error_propagates():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = WatchlistsService(mock_client)

    with patch("robin_stocks_mcp.services.watchlists.rh") as mock_rh:
        mock_rh.get_all_watchlists.side_effect = Exception("Connection failed")

        with pytest.raises(RobinhoodAPIError, match="Failed to fetch watchlists"):
            service.get_watchlists()


def test_get_watchlist_symbols_with_no_instruments():
    """Watchlist with no instruments returns empty symbols."""
    mock_client = MagicMock(spec=RobinhoodClient)
    service = WatchlistsService(mock_client)

    with patch("robin_stocks_mcp.services.watchlists.rh") as mock_rh:
        mock_rh.get_all_watchlists.return_value = {
            "results": [
                {"id": "abc-123", "display_name": "Empty List"},
            ]
        }
        mock_rh.get_watchlist_by_name.return_value = []

        watchlists = service.get_watchlists()

        assert len(watchlists) == 1
        assert watchlists[0].symbols == []
