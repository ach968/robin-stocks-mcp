# robin_stocks_mcp/services/news.py
from typing import List, Optional
import robin_stocks.robinhood as rh
from robin_stocks_mcp.models import NewsItem
from robin_stocks_mcp.robinhood.client import RobinhoodClient
from robin_stocks_mcp.robinhood.errors import RobinhoodAPIError


class NewsService:
    """Service for news operations."""
    
    def __init__(self, client: RobinhoodClient):
        self.client = client
    
    def get_news(self, symbol: Optional[str] = None) -> List[NewsItem]:
        """Get news for a symbol or general news."""
        self.client.ensure_session()
        
        try:
            if symbol:
                news_data = rh.get_news(symbol)
            else:
                # Get top news
                news_data = rh.get_top_news()
            
            if not news_data:
                return []
            
            items = []
            for item in news_data:
                news_item = NewsItem(
                    id=item.get('uuid', ''),
                    headline=item.get('title', ''),
                    summary=item.get('summary', ''),
                    source=item.get('source', ''),
                    url=item.get('url', ''),
                    published_at=item.get('published_at')
                )
                items.append(news_item)
            
            return items
        except Exception as e:
            raise RobinhoodAPIError(f"Failed to fetch news: {e}")
