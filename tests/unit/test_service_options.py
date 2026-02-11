# tests/unit/test_service_options.py
from unittest.mock import MagicMock, patch

import pytest

from robin_stocks_mcp.robinhood.client import RobinhoodClient
from robin_stocks_mcp.robinhood.errors import (
    InvalidArgumentError,
    RobinhoodAPIError,
)
from robin_stocks_mcp.services.options import OptionsService


# -- Fixtures -------------------------------------------------------

MOCK_INSTRUMENT_CALL = {
    "chain_symbol": "AAPL",
    "expiration_date": "2026-03-20",
    "strike_price": "150.00",
    "type": "call",
    "state": "active",
    "id": "abc-123",
}

MOCK_INSTRUMENT_PUT = {
    "chain_symbol": "AAPL",
    "expiration_date": "2026-03-20",
    "strike_price": "155.00",
    "type": "put",
    "state": "active",
    "id": "def-456",
}

# get_option_market_data returns [[{...}]] (list of list-of-dicts)
MOCK_MARKET_DATA = [
    [
        {
            "chain_symbol": "AAPL",
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
    ]
]


# -- Tests: initialisation & validation -----------------------------


def test_service_initialization():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = OptionsService(mock_client)
    assert service.client == mock_client


def test_get_options_chain_requires_symbol():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = OptionsService(mock_client)

    with pytest.raises(InvalidArgumentError, match="Symbol is required"):
        service.get_options_chain("")


def test_get_options_chain_calls_ensure_session():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = OptionsService(mock_client)

    with patch("robin_stocks_mcp.services.options.rh") as mock_rh:
        mock_rh.find_tradable_options.return_value = []
        mock_rh.get_latest_price.return_value = [None]

        service.get_options_chain("AAPL", "2026-03-20")

        mock_client.ensure_session.assert_called_once()


# -- Tests: chain listing (no strike_price) -------------------------


def test_chain_listing_with_expiration_date():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = OptionsService(mock_client)

    with patch("robin_stocks_mcp.services.options.rh") as mock_rh:
        mock_rh.find_tradable_options.return_value = [
            MOCK_INSTRUMENT_CALL,
            MOCK_INSTRUMENT_PUT,
        ]
        mock_rh.get_latest_price.return_value = ["152.00"]

        contracts = service.get_options_chain("AAPL", "2026-03-20")

        assert len(contracts) == 2
        assert contracts[0].symbol == "AAPL"
        assert contracts[0].strike == 150.0
        assert contracts[0].type == "call"
        assert contracts[0].expiration == "2026-03-20"
        # Instrument data has no bid/ask/greeks
        assert contracts[0].bid is None
        assert contracts[0].delta is None

        assert contracts[1].strike == 155.0
        assert contracts[1].type == "put"

        mock_rh.find_tradable_options.assert_called_once_with(
            "AAPL", expirationDate="2026-03-20", optionType=None
        )


def test_chain_listing_with_option_type():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = OptionsService(mock_client)

    with patch("robin_stocks_mcp.services.options.rh") as mock_rh:
        mock_rh.find_tradable_options.return_value = [MOCK_INSTRUMENT_CALL]
        mock_rh.get_latest_price.return_value = ["150.00"]

        contracts = service.get_options_chain("AAPL", "2026-03-20", option_type="call")

        assert len(contracts) == 1
        assert contracts[0].type == "call"
        mock_rh.find_tradable_options.assert_called_once_with(
            "AAPL", expirationDate="2026-03-20", optionType="call"
        )


def test_chain_listing_resolves_nearest_expiration():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = OptionsService(mock_client)

    with patch("robin_stocks_mcp.services.options.rh") as mock_rh:
        mock_rh.get_chains.return_value = {
            "expiration_dates": ["2026-03-20", "2026-04-17"]
        }
        mock_rh.find_tradable_options.return_value = [MOCK_INSTRUMENT_CALL]
        mock_rh.get_latest_price.return_value = ["150.00"]

        contracts = service.get_options_chain("AAPL")

        assert len(contracts) == 1
        assert contracts[0].expiration == "2026-03-20"

        mock_rh.get_chains.assert_called_once_with("AAPL")
        mock_rh.find_tradable_options.assert_called_once_with(
            "AAPL", expirationDate="2026-03-20", optionType=None
        )


def test_chain_listing_empty_expirations():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = OptionsService(mock_client)

    with patch("robin_stocks_mcp.services.options.rh") as mock_rh:
        mock_rh.get_chains.return_value = {"expiration_dates": []}

        contracts = service.get_options_chain("AAPL")

        assert len(contracts) == 0
        mock_rh.find_tradable_options.assert_not_called()


def test_chain_listing_chains_returns_none():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = OptionsService(mock_client)

    with patch("robin_stocks_mcp.services.options.rh") as mock_rh:
        mock_rh.get_chains.return_value = None

        contracts = service.get_options_chain("AAPL")

        assert len(contracts) == 0


def test_chain_listing_near_the_money_filter():
    """Strikes outside ±20% of current price are filtered out."""
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
        mock_rh.find_tradable_options.return_value = [far_otm, near_money]
        mock_rh.get_latest_price.return_value = ["100.00"]

        contracts = service.get_options_chain("TEST", "2026-03-20", option_type="call")

        assert len(contracts) == 1
        assert contracts[0].strike == 100.0


def test_chain_listing_no_price_skips_filter():
    """If current price unavailable, all strikes returned."""
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
        mock_rh.find_tradable_options.return_value = [far_otm, near_money]
        mock_rh.get_latest_price.return_value = [None]

        contracts = service.get_options_chain("TEST", "2026-03-20")

        assert len(contracts) == 2


def test_chain_listing_skips_none_items():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = OptionsService(mock_client)

    with patch("robin_stocks_mcp.services.options.rh") as mock_rh:
        mock_rh.find_tradable_options.return_value = [
            None,
            MOCK_INSTRUMENT_CALL,
            None,
        ]
        mock_rh.get_latest_price.return_value = ["150.00"]

        contracts = service.get_options_chain("AAPL", "2026-03-20")

        assert len(contracts) == 1
        assert contracts[0].strike == 150.0


# -- Tests: targeted lookup (with strike_price) ---------------------


def test_targeted_lookup_with_greeks():
    """strike_price uses get_option_market_data for full greeks."""
    mock_client = MagicMock(spec=RobinhoodClient)
    service = OptionsService(mock_client)

    with patch("robin_stocks_mcp.services.options.rh") as mock_rh:
        mock_rh.get_option_market_data.return_value = MOCK_MARKET_DATA

        contracts = service.get_options_chain(
            "AAPL", "2026-03-20", option_type="call", strike_price="150.00"
        )

        assert len(contracts) == 1
        c = contracts[0]
        assert c.bid == 5.50
        assert c.ask == 5.75
        assert c.mark_price == 5.625
        assert c.implied_volatility == 0.3245
        assert c.delta == 0.55
        assert c.gamma == 0.025
        assert c.theta == -0.05
        assert c.vega == 0.2
        assert c.rho == 0.08
        assert c.chance_of_profit_short == 0.45

        mock_rh.get_option_market_data.assert_called_once_with(
            "AAPL",
            expirationDate="2026-03-20",
            strikePrice="150.00",
            optionType="call",
        )
        # Should NOT use find_tradable_options for targeted lookup
        mock_rh.find_tradable_options.assert_not_called()


def test_targeted_lookup_both_types():
    """No option_type fetches both call and put."""
    mock_client = MagicMock(spec=RobinhoodClient)
    service = OptionsService(mock_client)

    with patch("robin_stocks_mcp.services.options.rh") as mock_rh:
        mock_rh.get_option_market_data.return_value = MOCK_MARKET_DATA

        service.get_options_chain("AAPL", "2026-03-20", strike_price="150.00")

        # Called twice: once for call, once for put
        assert mock_rh.get_option_market_data.call_count == 2


def test_targeted_lookup_empty_result():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = OptionsService(mock_client)

    with patch("robin_stocks_mcp.services.options.rh") as mock_rh:
        mock_rh.get_option_market_data.return_value = None

        contracts = service.get_options_chain(
            "AAPL", "2026-03-20", option_type="call", strike_price="999.00"
        )

        assert len(contracts) == 0


def test_targeted_lookup_none_entries():
    """None entries in market data are skipped."""
    mock_client = MagicMock(spec=RobinhoodClient)
    service = OptionsService(mock_client)

    with patch("robin_stocks_mcp.services.options.rh") as mock_rh:
        mock_rh.get_option_market_data.return_value = [[None]]

        contracts = service.get_options_chain(
            "AAPL", "2026-03-20", option_type="call", strike_price="150.00"
        )

        assert len(contracts) == 0


# -- Tests: error handling ------------------------------------------


def test_api_error_wrapped():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = OptionsService(mock_client)

    with patch("robin_stocks_mcp.services.options.rh") as mock_rh:
        mock_rh.find_tradable_options.side_effect = Exception("API Error")
        mock_rh.get_latest_price.return_value = [None]

        with pytest.raises(RobinhoodAPIError, match="Failed to fetch options chain"):
            service.get_options_chain("AAPL", "2026-03-20")
