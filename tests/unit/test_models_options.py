import pytest
from robin_stocks_mcp.models.options import OptionContract
from datetime import datetime


def test_option_contract_creation():
    contract = OptionContract(
        symbol="AAPL",
        expiration="2026-03-20",
        strike=150.0,
        type="call",
        bid=5.50,
        ask=5.75,
        open_interest=1000,
        volume=500
    )
    assert contract.symbol == "AAPL"
    assert contract.strike == 150.0
    assert contract.type == "call"
