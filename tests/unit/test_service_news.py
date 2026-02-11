# tests/unit/test_service_news.py
import pytest
from unittest.mock import MagicMock
from robin_stocks_mcp.services.news import NewsService
from robin_stocks_mcp.robinhood.client import RobinhoodClient


def test_service_initialization():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = NewsService(mock_client)
    assert service.client == mock_client
