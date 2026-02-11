import pytest
from robin_stocks_mcp.models.portfolio import PortfolioSummary, Position


def test_portfolio_summary_creation():
    summary = PortfolioSummary(
        equity=10000.50,
        cash=2500.0,
        buying_power=12500.0,
        unrealized_pl=500.25,
        day_change=25.50
    )
    assert summary.equity == 10000.50


def test_position_creation():
    position = Position(
        symbol="AAPL",
        quantity=100,
        average_cost=145.0,
        market_value=15050.0,
        unrealized_pl=500.0
    )
    assert position.symbol == "AAPL"
    assert position.quantity == 100
