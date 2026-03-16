from robinhood_core.models.fundamentals import Fundamentals


def test_fundamentals_creation():
    fundamentals = Fundamentals(
        market_cap=2500000000000.0,
        pe_ratio=28.5,
        dividend_yield=0.005,
        week_52_high=200.0,
        week_52_low=140.0,
    )
    assert fundamentals.pe_ratio == 28.5
