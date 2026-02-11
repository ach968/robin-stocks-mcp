from robin_stocks_mcp.models.options import OptionContract


def test_option_contract_creation():
    contract = OptionContract(
        symbol="AAPL",
        expiration="2026-03-20",
        strike=150.0,
        type="call",
        bid=5.50,
        ask=5.75,
        open_interest=1000,
        volume=500,
    )
    assert contract.symbol == "AAPL"
    assert contract.strike == 150.0
    assert contract.type == "call"


def test_option_contract_with_greeks():
    contract = OptionContract(
        symbol="AAPL",
        expiration="2026-03-20",
        strike=150.0,
        type="call",
        bid=5.50,
        ask=5.75,
        mark_price=5.625,
        last_trade_price=5.60,
        open_interest=1000,
        volume=500,
        implied_volatility="0.3245",
        delta="0.5500",
        gamma="0.0250",
        theta="-0.0500",
        vega="0.2000",
        rho="0.0800",
        chance_of_profit_short="0.4500",
        chance_of_profit_long="0.5500",
    )
    assert contract.implied_volatility == 0.3245
    assert contract.delta == 0.55
    assert contract.gamma == 0.025
    assert contract.theta == -0.05
    assert contract.vega == 0.2
    assert contract.rho == 0.08
    assert contract.chance_of_profit_short == 0.45
    assert contract.chance_of_profit_long == 0.55
    assert contract.mark_price == 5.625
    assert contract.last_trade_price == 5.60


def test_option_contract_greeks_none_by_default():
    contract = OptionContract(
        symbol="AAPL",
        expiration="2026-03-20",
        strike=150.0,
        type="call",
    )
    assert contract.delta is None
    assert contract.gamma is None
    assert contract.theta is None
    assert contract.vega is None
    assert contract.rho is None
    assert contract.implied_volatility is None
    assert contract.chance_of_profit_short is None
    assert contract.chance_of_profit_long is None
    assert contract.mark_price is None
    assert contract.last_trade_price is None


def test_option_contract_greeks_string_coercion():
    contract = OptionContract(
        symbol="AAPL",
        expiration="2026-03-20",
        strike="150.00",
        type="put",
        delta="-0.45",
        implied_volatility="0.30",
    )
    assert contract.strike == 150.0
    assert contract.delta == -0.45
    assert contract.implied_volatility == 0.30
