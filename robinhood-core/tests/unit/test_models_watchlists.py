from robinhood_core.models.watchlists import Watchlist


def test_watchlist_creation():
    watchlist = Watchlist(
        id="watchlist-123", name="My Watchlist", symbols=["AAPL", "GOOGL", "MSFT"]
    )
    assert watchlist.name == "My Watchlist"
    assert len(watchlist.symbols) == 3
