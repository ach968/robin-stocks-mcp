# tests/unit/test_service_options.py
from unittest.mock import MagicMock, patch

import pytest

from robin_stocks_mcp.robinhood.client import RobinhoodClient
from robin_stocks_mcp.robinhood.errors import InvalidArgumentError, RobinhoodAPIError
from robin_stocks_mcp.services.options import OptionsService

MOCK_OPTION_CALL = {
    "chain_symbol": "AAPL",
    "expiration_date": "2026-03-20",
    "strike_price": "150.00",
    "type": "call",
    "bid_price": "5.50",
    "ask_price": "5.75",
    "adjusted_mark_price": "5.625",
    "last_trade_price": "5.60",
    "open_interest": "1000",
    "volume": "500",
    "implied_volatility": "0.3245",
    "delta": "0.5500",
    "gamma": "0.0250",
    "theta": "-0.0500",
    "vega": "0.2000",
    "rho": "0.0800",
    "chance_of_profit_short": "0.4500",
    "chance_of_profit_long": "0.5500",
}

MOCK_OPTION_PUT = {
    "chain_symbol": "AAPL",
    "expiration_date": "2026-03-20",
    "strike_price": "155.00",
    "type": "put",
    "bid_price": "3.50",
    "ask_price": "3.75",
    "open_interest": "800",
    "volume": "300",
}


def test_service_initialization():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = OptionsService(mock_client)
    assert service.client == mock_client


def test_get_options_chain_requires_symbol():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = OptionsService(mock_client)

    with pytest.raises(InvalidArgumentError, match="Symbol is required"):
        service.get_options_chain("")


def test_get_options_chain_with_expiration_date():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = OptionsService(mock_client)

    with patch("robin_stocks_mcp.services.options.rh") as mock_rh:
        mock_rh.find_options_by_expiration.return_value = [
            MOCK_OPTION_CALL,
            MOCK_OPTION_PUT,
        ]
        # Mock current price so near-the-money filter includes both strikes
        mock_rh.get_latest_price.return_value = ["152.00"]

        contracts = service.get_options_chain("AAPL", "2026-03-20")

        assert len(contracts) == 2
        assert contracts[0].symbol == "AAPL"
        assert contracts[0].strike == 150.0
        assert contracts[0].type == "call"
        assert contracts[0].bid == 5.50
        assert contracts[0].ask == 5.75
        assert contracts[0].open_interest == 1000
        assert contracts[0].volume == 500
        assert contracts[0].expiration == "2026-03-20"

        # Verify greeks are populated
        assert contracts[0].implied_volatility == 0.3245
        assert contracts[0].delta == 0.55
        assert contracts[0].gamma == 0.025
        assert contracts[0].theta == -0.05
        assert contracts[0].vega == 0.2
        assert contracts[0].rho == 0.08
        assert contracts[0].mark_price == 5.625
        assert contracts[0].chance_of_profit_short == 0.45

        assert contracts[1].symbol == "AAPL"
        assert contracts[1].strike == 155.0
        assert contracts[1].type == "put"

        mock_rh.find_options_by_expiration.assert_called_once_with(
            "AAPL", expirationDate="2026-03-20", optionType=None
        )


def test_get_options_chain_with_option_type():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = OptionsService(mock_client)

    with patch("robin_stocks_mcp.services.options.rh") as mock_rh:
        mock_rh.find_options_by_expiration.return_value = [MOCK_OPTION_CALL]
        mock_rh.get_latest_price.return_value = ["150.00"]

        contracts = service.get_options_chain("AAPL", "2026-03-20", option_type="call")

        assert len(contracts) == 1
        assert contracts[0].type == "call"
        mock_rh.find_options_by_expiration.assert_called_once_with(
            "AAPL", expirationDate="2026-03-20", optionType="call"
        )


def test_get_options_chain_with_strike_price():
    """When strike_price is provided, uses find_options_by_expiration_and_strike."""
    mock_client = MagicMock(spec=RobinhoodClient)
    service = OptionsService(mock_client)

    with patch("robin_stocks_mcp.services.options.rh") as mock_rh:
        mock_rh.find_options_by_expiration_and_strike.return_value = [MOCK_OPTION_CALL]

        contracts = service.get_options_chain(
            "AAPL", "2026-03-20", option_type="call", strike_price="150.00"
        )

        assert len(contracts) == 1
        assert contracts[0].strike == 150.0
        mock_rh.find_options_by_expiration_and_strike.assert_called_once_with(
            "AAPL",
            expirationDate="2026-03-20",
            strikePrice="150.00",
            optionType="call",
        )
        # Should NOT call find_options_by_expiration for targeted lookup
        mock_rh.find_options_by_expiration.assert_not_called()


def test_get_options_chain_without_expiration_date():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = OptionsService(mock_client)

    mock_chains = {"expiration_dates": ["2026-03-20", "2026-04-17"]}

    with patch("robin_stocks_mcp.services.options.rh") as mock_rh:
        mock_rh.get_chains.return_value = mock_chains
        mock_rh.find_options_by_expiration.return_value = [MOCK_OPTION_CALL]
        mock_rh.get_latest_price.return_value = ["150.00"]

        contracts = service.get_options_chain("AAPL")

        assert len(contracts) == 1
        assert contracts[0].expiration == "2026-03-20"

        mock_rh.get_chains.assert_called_once_with("AAPL")
        mock_rh.find_options_by_expiration.assert_called_once_with(
            "AAPL", expirationDate="2026-03-20", optionType=None
        )


def test_get_options_chain_empty_expirations():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = OptionsService(mock_client)

    mock_chains = {"expiration_dates": []}

    with patch("robin_stocks_mcp.services.options.rh") as mock_rh:
        mock_rh.get_chains.return_value = mock_chains

        contracts = service.get_options_chain("AAPL")

        assert len(contracts) == 0
        mock_rh.find_options_by_expiration.assert_not_called()


def test_get_options_chain_near_the_money_filter():
    """Strikes outside ±20% of current price should be filtered out."""
    mock_client = MagicMock(spec=RobinhoodClient)
    service = OptionsService(mock_client)

    # Current price 100, so ±20% = 80-120
    far_otm = {
        "chain_symbol": "TEST",
        "strike_price": "200.00",
        "type": "call",
        "bid_price": "0.05",
        "ask_price": "0.10",
    }
    near_money = {
        "chain_symbol": "TEST",
        "strike_price": "100.00",
        "type": "call",
        "bid_price": "5.00",
        "ask_price": "5.50",
    }

    with patch("robin_stocks_mcp.services.options.rh") as mock_rh:
        mock_rh.find_options_by_expiration.return_value = [far_otm, near_money]
        mock_rh.get_latest_price.return_value = ["100.00"]

        contracts = service.get_options_chain("TEST", "2026-03-20", option_type="call")

        assert len(contracts) == 1
        assert contracts[0].strike == 100.0


def test_get_options_chain_no_price_skips_filter():
    """If current price can't be fetched, all strikes are returned."""
    mock_client = MagicMock(spec=RobinhoodClient)
    service = OptionsService(mock_client)

    far_otm = {
        "chain_symbol": "TEST",
        "strike_price": "200.00",
        "type": "call",
    }
    near_money = {
        "chain_symbol": "TEST",
        "strike_price": "100.00",
        "type": "call",
    }

    with patch("robin_stocks_mcp.services.options.rh") as mock_rh:
        mock_rh.find_options_by_expiration.return_value = [far_otm, near_money]
        mock_rh.get_latest_price.return_value = [None]

        contracts = service.get_options_chain("TEST", "2026-03-20")

        # Both returned because price fetch failed
        assert len(contracts) == 2


def test_get_options_chain_skips_none_items():
    """None items in the options data list should be skipped."""
    mock_client = MagicMock(spec=RobinhoodClient)
    service = OptionsService(mock_client)

    with patch("robin_stocks_mcp.services.options.rh") as mock_rh:
        mock_rh.find_options_by_expiration.return_value = [None, MOCK_OPTION_CALL, None]
        mock_rh.get_latest_price.return_value = ["150.00"]

        contracts = service.get_options_chain("AAPL", "2026-03-20")

        assert len(contracts) == 1
        assert contracts[0].strike == 150.0


def test_get_options_chain_api_error():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = OptionsService(mock_client)

    with patch("robin_stocks_mcp.services.options.rh") as mock_rh:
        mock_rh.find_options_by_expiration.side_effect = Exception("API Error")

        with pytest.raises(RobinhoodAPIError, match="Failed to fetch options chain"):
            service.get_options_chain("AAPL", "2026-03-20")


def test_get_options_chain_calls_ensure_session():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = OptionsService(mock_client)

    with patch("robin_stocks_mcp.services.options.rh") as mock_rh:
        mock_rh.find_options_by_expiration.return_value = []

        service.get_options_chain("AAPL", "2026-03-20")

        mock_client.ensure_session.assert_called_once()


def test_get_options_chain_chains_returns_none():
    """If get_chains returns None, return empty list."""
    mock_client = MagicMock(spec=RobinhoodClient)
    service = OptionsService(mock_client)

    with patch("robin_stocks_mcp.services.options.rh") as mock_rh:
        mock_rh.get_chains.return_value = None

        contracts = service.get_options_chain("AAPL")

        assert len(contracts) == 0


def test_get_options_chain_strike_price_empty_result():
    """Strike price lookup with no matching contracts."""
    mock_client = MagicMock(spec=RobinhoodClient)
    service = OptionsService(mock_client)

    with patch("robin_stocks_mcp.services.options.rh") as mock_rh:
        mock_rh.find_options_by_expiration_and_strike.return_value = [None]

        contracts = service.get_options_chain(
            "AAPL", "2026-03-20", strike_price="999.00"
        )

        assert len(contracts) == 0
