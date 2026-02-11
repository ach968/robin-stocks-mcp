# robin_stocks_mcp/services/news.py
from typing import List
import requests
import robin_stocks.robinhood as rh
from robin_stocks_mcp.models import NewsItem
from robin_stocks_mcp.robinhood.client import RobinhoodClient
from robin_stocks_mcp.robinhood.errors import (
    AuthRequiredError,
    InvalidArgumentError,
    RobinhoodAPIError,
)


class NewsService:
    """Service for news operations."""

    def __init__(self, client: RobinhoodClient):
        self.client = client

    def get_news(self, symbol: str) -> List[NewsItem]:
        """Get news for a symbol.

        :param symbol: Stock ticker symbol (required).
        :raises InvalidArgumentError: If symbol is not provided.
        """
        if not symbol:
            raise InvalidArgumentError(
                "A stock symbol is required to fetch news."
            )

        self.client.ensure_session()

        try:
            news_data = rh.get_news(symbol)

            if not news_data:
                return []

            items = []
            for item in news_data:
                if not isinstance(item, dict):
                    continue
                news_item = NewsItem(
                    id=item.get("uuid", ""),
                    headline=item.get("title", ""),
                    summary=item.get("summary", ""),
                    source=item.get("source", ""),
                    url=item.get("url", ""),
                    published_at=item.get("published_at"),
                )
                items.append(news_item)

            return items
        except (RobinhoodAPIError, InvalidArgumentError, AuthRequiredError):
            raise
        except (requests.RequestException, ConnectionError, TimeoutError) as e:
            raise RobinhoodAPIError(f"Failed to fetch news: {e}") from e
        except Exception as e:
            raise RobinhoodAPIError(f"Failed to fetch news: {e}") from e
