from robinhood_core.models.news import NewsItem


def test_news_item_creation():
    item = NewsItem(
        id="news-123",
        headline="Apple releases new product",
        summary="Summary here",
        source="TechCrunch",
        url="https://techcrunch.com/article",
        published_at="2026-02-11T10:00:00Z",
    )
    assert item.headline == "Apple releases new product"
