# tests/unit/test_service_market_data.py
import pytest
from unittest.mock import MagicMock, patch
from robin_stocks_mcp.services.market_data import MarketDataService
from robin_stocks_mcp.robinhood.client import RobinhoodClient


def test_service_initialization():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = MarketDataService(mock_client)
    assert service.client == mock_client


def test_get_current_price_empty_symbols():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = MarketDataService(mock_client)
    
    from robin_stocks_mcp.robinhood.errors import InvalidArgumentError
    with pytest.raises(InvalidArgumentError):
        service.get_current_price([])


@patch('robin_stocks_mcp.services.market_data.rh')
def test_get_current_price_single_symbol(mock_rh):
    mock_client = MagicMock(spec=RobinhoodClient)
    service = MarketDataService(mock_client)
    
    mock_rh.get_quotes.return_value = {
        'symbol': 'AAPL',
        'last_trade_price': '150.50',
        'bid_price': '150.45',
        'ask_price': '150.55',
        'updated_at': '2026-02-11T10:00:00Z',
        'previous_close': '149.00',
        'change_percent': '1.01'
    }
    
    quotes = service.get_current_price(['AAPL'])
    
    assert len(quotes) == 1
    assert quotes[0].symbol == 'AAPL'
    assert quotes[0].last_price == 150.50
    assert quotes[0].bid == 150.45
    assert quotes[0].ask == 150.55
    mock_client.ensure_session.assert_called_once()


@patch('robin_stocks_mcp.services.market_data.rh')
def test_get_current_price_multiple_symbols(mock_rh):
    mock_client = MagicMock(spec=RobinhoodClient)
    service = MarketDataService(mock_client)
    
    mock_rh.get_quotes.return_value = [
        {
            'symbol': 'AAPL',
            'last_trade_price': '150.50',
            'updated_at': '2026-02-11T10:00:00Z'
        },
        {
            'symbol': 'GOOGL',
            'last_trade_price': '2800.00',
            'updated_at': '2026-02-11T10:00:00Z'
        }
    ]
    
    quotes = service.get_current_price(['AAPL', 'GOOGL'])
    
    assert len(quotes) == 2
    assert quotes[0].symbol == 'AAPL'
    assert quotes[1].symbol == 'GOOGL'


@patch('robin_stocks_mcp.services.market_data.rh')
def test_get_current_price_no_data(mock_rh):
    mock_client = MagicMock(spec=RobinhoodClient)
    service = MarketDataService(mock_client)
    
    mock_rh.get_quotes.return_value = None
    
    quotes = service.get_current_price(['INVALID'])
    
    assert len(quotes) == 0


def test_get_price_history_empty_symbol():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = MarketDataService(mock_client)
    
    from robin_stocks_mcp.robinhood.errors import InvalidArgumentError
    with pytest.raises(InvalidArgumentError):
        service.get_price_history('')


def test_get_price_history_invalid_interval():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = MarketDataService(mock_client)
    
    from robin_stocks_mcp.robinhood.errors import InvalidArgumentError
    with pytest.raises(InvalidArgumentError):
        service.get_price_history('AAPL', interval='invalid')


def test_get_price_history_invalid_span():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = MarketDataService(mock_client)
    
    from robin_stocks_mcp.robinhood.errors import InvalidArgumentError
    with pytest.raises(InvalidArgumentError):
        service.get_price_history('AAPL', span='invalid')


def test_get_price_history_invalid_bounds():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = MarketDataService(mock_client)
    
    from robin_stocks_mcp.robinhood.errors import InvalidArgumentError
    with pytest.raises(InvalidArgumentError):
        service.get_price_history('AAPL', bounds='invalid')


@patch('robin_stocks_mcp.services.market_data.rh')
def test_get_price_history_success(mock_rh):
    mock_client = MagicMock(spec=RobinhoodClient)
    service = MarketDataService(mock_client)
    
    mock_rh.get_stock_historicals.return_value = [
        {
            'begins_at': '2026-02-10T10:00:00Z',
            'open_price': '150.0',
            'high_price': '151.0',
            'low_price': '149.0',
            'close_price': '150.5',
            'volume': '1000000'
        }
    ]
    
    candles = service.get_price_history('AAPL', interval='day', span='week', bounds='regular')
    
    assert len(candles) == 1
    assert candles[0].open == 150.0
    assert candles[0].high == 151.0
    assert candles[0].low == 149.0
    assert candles[0].close == 150.5
    assert candles[0].volume == 1000000
    mock_client.ensure_session.assert_called_once()
    mock_rh.get_stock_historicals.assert_called_once_with(
        'AAPL', interval='day', span='week', bounds='regular'
    )


@patch('robin_stocks_mcp.services.market_data.rh')
def test_get_price_history_no_data(mock_rh):
    mock_client = MagicMock(spec=RobinhoodClient)
    service = MarketDataService(mock_client)
    
    mock_rh.get_stock_historicals.return_value = None
    
    candles = service.get_price_history('AAPL')
    
    assert len(candles) == 0
