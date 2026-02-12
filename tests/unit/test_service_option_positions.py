# tests/unit/test_service_option_positions.py
import pytest
from unittest.mock import MagicMock, patch
from robin_stocks_mcp.services.options import OptionsService
from robin_stocks_mcp.robinhood.client import RobinhoodClient
from robin_stocks_mcp.robinhood.errors import RobinhoodAPIError


MOCK_POSITION = {
    "option": "https://api.robinhood.com/options/instruments/abc-123/",
    "chain_symbol": "AAPL",
    "type": "short",
    "quantity": "2.0000",
    "average_price": "3.5000",
    "created_at": "2025-01-15T10:00:00Z",
    "updated_at": "2025-02-01T15:30:00Z",
}

MOCK_INSTRUMENT = {
    "strike_price": "150.0000",
    "expiration_date": "2026-03-20",
    "type": "put",
    "chain_symbol": "AAPL",
}


def test_get_option_positions_success():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = OptionsService(mock_client)

    with patch("robin_stocks_mcp.services.options.rh") as mock_rh:
        mock_rh.get_open_option_positions.return_value = [MOCK_POSITION]
        mock_rh.get_option_instrument_data_by_id.return_value = MOCK_INSTRUMENT

        positions = service.get_option_positions()

        assert len(positions) == 1
        pos = positions[0]
        assert pos.symbol == "AAPL"
        assert pos.strike_price == 150.0
        assert pos.expiration_date == "2026-03-20"
        assert pos.option_type == "put"
        assert pos.direction == "short"
        assert pos.quantity == 2.0
        assert pos.average_price == 3.5
        assert pos.created_at == "2025-01-15T10:00:00Z"
        assert pos.updated_at == "2025-02-01T15:30:00Z"

        mock_rh.get_open_option_positions.assert_called_once()
        mock_rh.get_option_instrument_data_by_id.assert_called_once_with("abc-123")


def test_get_option_positions_empty():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = OptionsService(mock_client)

    with patch("robin_stocks_mcp.services.options.rh") as mock_rh:
        mock_rh.get_open_option_positions.return_value = []

        positions = service.get_option_positions()
        assert positions == []


def test_get_option_positions_none_response():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = OptionsService(mock_client)

    with patch("robin_stocks_mcp.services.options.rh") as mock_rh:
        mock_rh.get_open_option_positions.return_value = None

        positions = service.get_option_positions()
        assert positions == []


def test_get_option_positions_none_items_filtered():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = OptionsService(mock_client)

    with patch("robin_stocks_mcp.services.options.rh") as mock_rh:
        mock_rh.get_open_option_positions.return_value = [None, MOCK_POSITION, None]
        mock_rh.get_option_instrument_data_by_id.return_value = MOCK_INSTRUMENT

        positions = service.get_option_positions()
        assert len(positions) == 1
        assert positions[0].symbol == "AAPL"


def test_get_option_positions_instrument_resolve_failure():
    """When instrument resolution fails, position still returned with partial data."""
    mock_client = MagicMock(spec=RobinhoodClient)
    service = OptionsService(mock_client)

    with patch("robin_stocks_mcp.services.options.rh") as mock_rh:
        mock_rh.get_open_option_positions.return_value = [MOCK_POSITION]
        mock_rh.get_option_instrument_data_by_id.side_effect = Exception("503 Error")

        positions = service.get_option_positions()

        assert len(positions) == 1
        pos = positions[0]
        # Symbol comes from chain_symbol on the position itself
        assert pos.symbol == "AAPL"
        assert pos.direction == "short"
        assert pos.quantity == 2.0
        # These are None because instrument resolution failed
        assert pos.strike_price is None
        assert pos.expiration_date is None
        assert pos.option_type is None


def test_get_option_positions_multiple():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = OptionsService(mock_client)

    position_2 = {
        "option": "https://api.robinhood.com/options/instruments/def-456/",
        "chain_symbol": "TSLA",
        "type": "long",
        "quantity": "1.0000",
        "average_price": "12.0000",
        "created_at": "2025-02-01T09:00:00Z",
        "updated_at": "2025-02-10T12:00:00Z",
    }

    instrument_2 = {
        "strike_price": "250.0000",
        "expiration_date": "2026-04-17",
        "type": "call",
        "chain_symbol": "TSLA",
    }

    with patch("robin_stocks_mcp.services.options.rh") as mock_rh:
        mock_rh.get_open_option_positions.return_value = [MOCK_POSITION, position_2]
        mock_rh.get_option_instrument_data_by_id.side_effect = [
            MOCK_INSTRUMENT,
            instrument_2,
        ]

        positions = service.get_option_positions()

        assert len(positions) == 2
        assert positions[0].symbol == "AAPL"
        assert positions[0].strike_price == 150.0
        assert positions[0].option_type == "put"
        assert positions[1].symbol == "TSLA"
        assert positions[1].strike_price == 250.0
        assert positions[1].option_type == "call"
        assert positions[1].direction == "long"


def test_get_option_positions_calls_ensure_session():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = OptionsService(mock_client)

    with patch("robin_stocks_mcp.services.options.rh") as mock_rh:
        mock_rh.get_open_option_positions.return_value = []

        service.get_option_positions()

        mock_client.ensure_session.assert_called_once()


def test_get_option_positions_api_error():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = OptionsService(mock_client)

    with patch("robin_stocks_mcp.services.options.rh") as mock_rh:
        mock_rh.get_open_option_positions.side_effect = Exception("API Error")

        with pytest.raises(RobinhoodAPIError, match="Failed to fetch option positions"):
            service.get_option_positions()


def test_get_option_positions_string_values_coerced():
    """Test that string numeric values from API are properly coerced."""
    mock_client = MagicMock(spec=RobinhoodClient)
    service = OptionsService(mock_client)

    with patch("robin_stocks_mcp.services.options.rh") as mock_rh:
        mock_rh.get_open_option_positions.return_value = [MOCK_POSITION]
        mock_rh.get_option_instrument_data_by_id.return_value = MOCK_INSTRUMENT

        positions = service.get_option_positions()

        pos = positions[0]
        assert isinstance(pos.quantity, float)
        assert isinstance(pos.average_price, float)
        assert isinstance(pos.strike_price, float)


def test_get_option_positions_no_option_url():
    """Test position with missing option URL still processes."""
    mock_client = MagicMock(spec=RobinhoodClient)
    service = OptionsService(mock_client)

    position_no_url = {
        "option": None,
        "chain_symbol": "SPY",
        "type": "long",
        "quantity": "5.0000",
        "average_price": "1.2500",
        "created_at": None,
        "updated_at": None,
    }

    with patch("robin_stocks_mcp.services.options.rh") as mock_rh:
        mock_rh.get_open_option_positions.return_value = [position_no_url]

        positions = service.get_option_positions()

        assert len(positions) == 1
        assert positions[0].symbol == "SPY"
        assert positions[0].direction == "long"
        assert positions[0].strike_price is None
        assert positions[0].expiration_date is None
