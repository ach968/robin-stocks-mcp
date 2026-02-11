# tests/unit/test_service_news.py
from unittest.mock import MagicMock, patch
from robin_stocks_mcp.services.news import NewsService
from robin_stocks_mcp.robinhood.client import RobinhoodClient
from robin_stocks_mcp.robinhood.errors import InvalidArgumentError, RobinhoodAPIError
import pytest


def test_service_initialization():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = NewsService(mock_client)
    assert service.client == mock_client


def test_get_news_requires_symbol():
    """get_news raises InvalidArgumentError when symbol is empty or None."""
    mock_client = MagicMock(spec=RobinhoodClient)
    service = NewsService(mock_client)

    with pytest.raises(InvalidArgumentError, match="symbol is required"):
        service.get_news("")

    with pytest.raises(InvalidArgumentError, match="symbol is required"):
        service.get_news(None)  # type: ignore[arg-type]


def test_get_news_returns_items():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = NewsService(mock_client)

    with patch("robin_stocks_mcp.services.news.rh") as mock_rh:
        mock_rh.get_news.return_value = [
            {
                "uuid": "news-1",
                "title": "Apple Earnings Beat",
                "summary": "Apple reported Q4 earnings above expectations.",
                "source": "Reuters",
                "url": "https://example.com/news/1",
                "published_at": "2026-02-11T10:00:00Z",
            },
            {
                "uuid": "news-2",
                "title": "Apple New Product",
                "summary": "Apple announces new product line.",
                "source": "Bloomberg",
                "url": "https://example.com/news/2",
                "published_at": "2026-02-11T11:00:00Z",
            },
        ]

        items = service.get_news("AAPL")

        assert len(items) == 2
        assert items[0].id == "news-1"
        assert items[0].headline == "Apple Earnings Beat"
        assert items[0].source == "Reuters"
        assert items[1].id == "news-2"
        assert items[1].headline == "Apple New Product"
        mock_client.ensure_session.assert_called_once()
        mock_rh.get_news.assert_called_once_with("AAPL")


def test_get_news_empty_response():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = NewsService(mock_client)

    with patch("robin_stocks_mcp.services.news.rh") as mock_rh:
        mock_rh.get_news.return_value = []

        items = service.get_news("XYZ")

        assert items == []


def test_get_news_none_response():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = NewsService(mock_client)

    with patch("robin_stocks_mcp.services.news.rh") as mock_rh:
        mock_rh.get_news.return_value = None

        items = service.get_news("XYZ")

        assert items == []


def test_get_news_api_error_propagates():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = NewsService(mock_client)

    with patch("robin_stocks_mcp.services.news.rh") as mock_rh:
        mock_rh.get_news.side_effect = Exception("Connection failed")

        with pytest.raises(RobinhoodAPIError, match="Failed to fetch news"):
            service.get_news("AAPL")


def test_get_news_skips_non_dict_items():
    """Non-dict items in the response are skipped."""
    mock_client = MagicMock(spec=RobinhoodClient)
    service = NewsService(mock_client)

    with patch("robin_stocks_mcp.services.news.rh") as mock_rh:
        mock_rh.get_news.return_value = [
            {
                "uuid": "news-1",
                "title": "Valid Item",
                "summary": "Summary",
                "source": "Reuters",
                "url": "https://example.com",
                "published_at": "2026-02-11T10:00:00Z",
            },
            None,  # non-dict item
            "garbage",  # non-dict item
        ]

        items = service.get_news("AAPL")

        assert len(items) == 1
        assert items[0].headline == "Valid Item"
