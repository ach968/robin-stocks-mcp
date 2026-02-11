# tests/unit/test_robinhood_client.py
import pytest
from unittest.mock import patch, MagicMock
import os


def test_client_initialization():
    from robin_stocks_mcp.robinhood.client import RobinhoodClient
    
    client = RobinhoodClient()
    assert client._authenticated is False
    assert client._username is None
    assert client._password is None


def test_lazy_auth_on_ensure_session():
    from robin_stocks_mcp.robinhood.client import RobinhoodClient
    
    with patch.dict(os.environ, {
        'RH_USERNAME': 'test_user',
        'RH_PASSWORD': 'test_pass'
    }):
        client = RobinhoodClient()
        # Should not be authenticated yet
        assert client._authenticated is False


def test_client_loads_config_from_env():
    from robin_stocks_mcp.robinhood.client import RobinhoodClient
    
    with patch.dict(os.environ, {
        'RH_USERNAME': 'test_user',
        'RH_PASSWORD': 'test_pass',
        'RH_SESSION_PATH': '/tmp/test_session.json',
        'RH_ALLOW_MFA': '1'
    }):
        client = RobinhoodClient()
        assert client._username == 'test_user'
        assert client._password == 'test_pass'
        assert client._session_path == '/tmp/test_session.json'
        assert client._allow_mfa is True


def test_auth_required_error_when_no_credentials():
    from robin_stocks_mcp.robinhood.client import RobinhoodClient
    from robin_stocks_mcp.robinhood.errors import AuthRequiredError
    
    with patch.dict(os.environ, {}, clear=True):
        client = RobinhoodClient()
        with pytest.raises(AuthRequiredError):
            client.ensure_session()


def test_error_classes_exist():
    from robin_stocks_mcp.robinhood.errors import (
        RobinhoodError,
        AuthRequiredError,
        InvalidArgumentError,
        RobinhoodAPIError,
        NetworkError,
    )
    
    # Verify error hierarchy
    assert issubclass(AuthRequiredError, RobinhoodError)
    assert issubclass(InvalidArgumentError, RobinhoodError)
    assert issubclass(RobinhoodAPIError, RobinhoodError)
    assert issubclass(NetworkError, RobinhoodError)


def test_robinhood_client_exported():
    from robin_stocks_mcp.robinhood import RobinhoodClient
    from robin_stocks_mcp.robinhood import (
        RobinhoodError,
        AuthRequiredError,
        InvalidArgumentError,
        RobinhoodAPIError,
        NetworkError,
    )
    assert RobinhoodClient is not None
    assert RobinhoodError is not None
    assert AuthRequiredError is not None
