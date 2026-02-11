# tests/unit/test_service_watchlists.py
import pytest
from unittest.mock import MagicMock
from robin_stocks_mcp.services.watchlists import WatchlistsService
from robin_stocks_mcp.robinhood.client import RobinhoodClient


def test_service_initialization():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = WatchlistsService(mock_client)
    assert service.client == mock_client
