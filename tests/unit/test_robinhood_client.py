# tests/unit/test_robinhood_client.py
import pytest
from unittest.mock import patch, MagicMock
import os
from pathlib import Path


def test_client_initialization():
    from robin_stocks_mcp.robinhood.client import RobinhoodClient

    client = RobinhoodClient()
    assert client._authenticated is False
    assert client._username is None
    assert client._password is None


def test_lazy_auth_on_ensure_session():
    from robin_stocks_mcp.robinhood.client import RobinhoodClient

    with patch.dict(
        os.environ, {"RH_USERNAME": "test_user", "RH_PASSWORD": "test_pass"}
    ):
        client = RobinhoodClient()
        # Should not be authenticated yet
        assert client._authenticated is False


def test_client_loads_config_from_env():
    from robin_stocks_mcp.robinhood.client import RobinhoodClient

    with patch.dict(
        os.environ,
        {
            "RH_USERNAME": "test_user",
            "RH_PASSWORD": "test_pass",
            "RH_SESSION_PATH": "/tmp/test_session",
            "RH_ALLOW_MFA": "1",
        },
    ):
        client = RobinhoodClient()
        assert client._username == "test_user"
        assert client._password == "test_pass"
        assert client._session_path == "/tmp/test_session"
        assert client._allow_mfa is True


def test_client_accepts_explicit_args():
    from robin_stocks_mcp.robinhood.client import RobinhoodClient

    client = RobinhoodClient(
        username="arg_user",
        password="arg_pass",
        session_path="/tmp/arg_session",
        allow_mfa=True,
    )
    assert client._username == "arg_user"
    assert client._password == "arg_pass"
    assert client._session_path == "/tmp/arg_session"
    assert client._allow_mfa is True


def test_explicit_args_override_env():
    from robin_stocks_mcp.robinhood.client import RobinhoodClient

    with patch.dict(
        os.environ,
        {
            "RH_USERNAME": "env_user",
            "RH_PASSWORD": "env_pass",
            "RH_SESSION_PATH": "/tmp/env_session",
            "RH_ALLOW_MFA": "1",
        },
    ):
        client = RobinhoodClient(
            username="arg_user",
            password="arg_pass",
            session_path="/tmp/arg_session",
            allow_mfa=False,
        )
        assert client._username == "arg_user"
        assert client._password == "arg_pass"
        assert client._session_path == "/tmp/arg_session"
        assert client._allow_mfa is False


def test_explicit_args_none_falls_back_to_env():
    from robin_stocks_mcp.robinhood.client import RobinhoodClient

    with patch.dict(
        os.environ,
        {
            "RH_USERNAME": "env_user",
            "RH_PASSWORD": "env_pass",
        },
    ):
        client = RobinhoodClient(username=None, password=None)
        assert client._username == "env_user"
        assert client._password == "env_pass"


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
    )

    assert RobinhoodClient is not None
    assert RobinhoodError is not None
    assert AuthRequiredError is not None


def test_ensure_session_calls_rh_login():
    """rh.login is called with correct kwargs including pickle_path."""
    from robin_stocks_mcp.robinhood.client import RobinhoodClient

    client = RobinhoodClient(
        username="user",
        password="pass",
        session_path="/tmp/sessions",
    )

    with patch("robin_stocks_mcp.robinhood.client.rh") as mock_rh:
        mock_rh.login.return_value = {"access_token": "tok123"}
        result = client.ensure_session()

        mock_rh.login.assert_called_once_with(
            username="user",
            password="pass",
            store_session=True,
            pickle_path="/tmp/sessions",
        )
        assert result is client
        assert client._authenticated is True


def test_ensure_session_without_session_path():
    """When no session_path, pickle_path is not passed to rh.login."""
    from robin_stocks_mcp.robinhood.client import RobinhoodClient

    client = RobinhoodClient(username="user", password="pass")

    with patch("robin_stocks_mcp.robinhood.client.rh") as mock_rh:
        mock_rh.login.return_value = {"access_token": "tok123"}
        client.ensure_session()

        mock_rh.login.assert_called_once_with(
            username="user",
            password="pass",
            store_session=True,
        )


def test_ensure_session_with_mfa():
    """MFA code is passed through when allow_mfa is True."""
    from robin_stocks_mcp.robinhood.client import RobinhoodClient

    client = RobinhoodClient(
        username="user", password="pass", allow_mfa=True
    )

    with patch("robin_stocks_mcp.robinhood.client.rh") as mock_rh:
        mock_rh.login.return_value = {"access_token": "tok123"}
        client.ensure_session(mfa_code="123456")

        mock_rh.login.assert_called_once_with(
            username="user",
            password="pass",
            store_session=True,
            mfa_code="123456",
        )


def test_ensure_session_mfa_ignored_when_not_allowed():
    """MFA code is NOT passed when allow_mfa is False."""
    from robin_stocks_mcp.robinhood.client import RobinhoodClient

    client = RobinhoodClient(
        username="user", password="pass", allow_mfa=False
    )

    with patch("robin_stocks_mcp.robinhood.client.rh") as mock_rh:
        mock_rh.login.return_value = {"access_token": "tok123"}
        client.ensure_session(mfa_code="123456")

        mock_rh.login.assert_called_once_with(
            username="user",
            password="pass",
            store_session=True,
        )


def test_ensure_session_skips_login_when_already_authenticated():
    """Second call to ensure_session returns immediately."""
    from robin_stocks_mcp.robinhood.client import RobinhoodClient

    client = RobinhoodClient(username="user", password="pass")

    with patch("robin_stocks_mcp.robinhood.client.rh") as mock_rh:
        mock_rh.login.return_value = {"access_token": "tok123"}
        client.ensure_session()
        client.ensure_session()

        # Should only call login once
        assert mock_rh.login.call_count == 1


def test_ensure_session_login_returns_none():
    """AuthRequiredError raised when rh.login returns None."""
    from robin_stocks_mcp.robinhood.client import RobinhoodClient
    from robin_stocks_mcp.robinhood.errors import AuthRequiredError

    client = RobinhoodClient(username="user", password="pass")

    with patch("robin_stocks_mcp.robinhood.client.rh") as mock_rh:
        mock_rh.login.return_value = None
        with pytest.raises(AuthRequiredError, match="Login failed"):
            client.ensure_session()


def test_ensure_session_challenge_exception():
    """AuthRequiredError raised on challenge exception."""
    from robin_stocks_mcp.robinhood.client import RobinhoodClient
    from robin_stocks_mcp.robinhood.errors import AuthRequiredError

    client = RobinhoodClient(username="user", password="pass")

    with patch("robin_stocks_mcp.robinhood.client.rh") as mock_rh:
        mock_rh.login.side_effect = Exception("challenge required")
        with pytest.raises(AuthRequiredError, match="challenge"):
            client.ensure_session()


def test_ensure_session_network_exception():
    """NetworkError raised on generic exception."""
    from robin_stocks_mcp.robinhood.client import RobinhoodClient
    from robin_stocks_mcp.robinhood.errors import NetworkError

    client = RobinhoodClient(username="user", password="pass")

    with patch("robin_stocks_mcp.robinhood.client.rh") as mock_rh:
        mock_rh.login.side_effect = Exception("connection refused")
        with pytest.raises(NetworkError, match="Failed to authenticate"):
            client.ensure_session()


def test_logout_calls_rh_logout():
    """logout() calls rh.logout() and clears state."""
    from robin_stocks_mcp.robinhood.client import RobinhoodClient

    client = RobinhoodClient(username="user", password="pass")
    client._authenticated = True

    with patch("robin_stocks_mcp.robinhood.client.rh") as mock_rh:
        client.logout()

        mock_rh.logout.assert_called_once()
        assert client._authenticated is False


def test_logout_removes_pickle_file(tmp_path):
    """logout() removes the pickle file from session_path."""
    from robin_stocks_mcp.robinhood.client import RobinhoodClient

    pickle_file = tmp_path / "robinhood.pickle"
    pickle_file.write_bytes(b"fake pickle data")
    assert pickle_file.exists()

    client = RobinhoodClient(
        username="user", password="pass", session_path=str(tmp_path)
    )
    client._authenticated = True

    with patch("robin_stocks_mcp.robinhood.client.rh"):
        client.logout()

    assert not pickle_file.exists()
    assert client._authenticated is False


def test_logout_no_session_path():
    """logout() works without session_path (no file to delete)."""
    from robin_stocks_mcp.robinhood.client import RobinhoodClient

    client = RobinhoodClient(username="user", password="pass")
    client._authenticated = True

    with patch("robin_stocks_mcp.robinhood.client.rh") as mock_rh:
        client.logout()

        mock_rh.logout.assert_called_once()
        assert client._authenticated is False


def test_logout_missing_pickle_no_error(tmp_path):
    """logout() doesn't raise when pickle file doesn't exist."""
    from robin_stocks_mcp.robinhood.client import RobinhoodClient

    client = RobinhoodClient(
        username="user", password="pass", session_path=str(tmp_path)
    )
    client._authenticated = True

    with patch("robin_stocks_mcp.robinhood.client.rh"):
        # Should not raise even though no pickle file exists
        client.logout()

    assert client._authenticated is False


def test_no_save_session_or_load_session_methods():
    """Verify the useless JSON session methods have been removed."""
    from robin_stocks_mcp.robinhood.client import RobinhoodClient

    client = RobinhoodClient()
    assert not hasattr(client, "_save_session")
    assert not hasattr(client, "_load_session")
    assert not hasattr(client, "_is_session_valid")
