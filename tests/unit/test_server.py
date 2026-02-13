# tests/unit/test_server.py
import pytest
from unittest.mock import MagicMock, patch


def test_server_imports():
    from robin_stocks_mcp.server import mcp

    assert mcp is not None


def test_server_has_list_tools():
    from robin_stocks_mcp.server import mcp

    assert hasattr(mcp, "list_tools")


def test_server_has_call_tool():
    from robin_stocks_mcp.server import mcp

    assert hasattr(mcp, "call_tool")


def test_parse_args_defaults():
    from robin_stocks_mcp.server import parse_args

    args = parse_args([])
    assert args.username is None
    assert args.password is None
    assert args.session_path is None
    assert args.allow_mfa is None


def test_parse_args_with_values():
    from robin_stocks_mcp.server import parse_args

    args = parse_args(
        [
            "--username",
            "myuser",
            "--password",
            "mypass",
            "--session-path",
            "/tmp/session.json",
            "--allow-mfa",
        ]
    )
    assert args.username == "myuser"
    assert args.password == "mypass"
    assert args.session_path == "/tmp/session.json"
    assert args.allow_mfa is True


def test_init_services_creates_all_services():
    from robin_stocks_mcp.server import _init_services
    import robin_stocks_mcp.server as srv

    _init_services(username="u", password="p")
    assert srv.client is not None
    assert srv.market_service is not None
    assert srv.options_service is not None
    assert srv.portfolio_service is not None
    assert srv.watchlists_service is not None
    assert srv.news_service is not None
    assert srv.fundamentals_service is not None
    assert srv.client._username == "u"
    assert srv.client._password == "p"


def test_init_services_passes_all_args():
    from robin_stocks_mcp.server import _init_services
    import robin_stocks_mcp.server as srv

    _init_services(
        username="u",
        password="p",
        session_path="/tmp/s.json",
        allow_mfa=True,
    )
    assert srv.client._username == "u"
    assert srv.client._password == "p"
    assert srv.client._session_path == "/tmp/s.json"
    assert srv.client._allow_mfa is True


@pytest.mark.asyncio
async def test_list_tools_returns_tools():
    from robin_stocks_mcp.server import list_tools

    tools = await list_tools()
    assert len(tools) == 11

    tool_names = [tool.name for tool in tools]
    expected_tools = [
        "robinhood.market.current_price",
        "robinhood.market.price_history",
        "robinhood.market.quote",
        "robinhood.options.chain",
        "robinhood.options.positions",
        "robinhood.portfolio.summary",
        "robinhood.portfolio.positions",
        "robinhood.watchlists.list",
        "robinhood.news.latest",
        "robinhood.fundamentals.get",
        "robinhood.auth.status",
    ]
    for expected in expected_tools:
        assert expected in tool_names


@pytest.mark.asyncio
async def test_call_tool_current_price():
    from robin_stocks_mcp.server import call_tool

    with patch("robin_stocks_mcp.server.market_service") as mock_service:
        mock_quote = MagicMock()
        mock_quote.model_dump.return_value = {
            "symbol": "AAPL",
            "last_price": 150.50,
            "timestamp": "2026-02-11T10:00:00Z",
        }
        mock_service.get_current_price.return_value = [mock_quote]

        result = await call_tool(
            "robinhood.market.current_price", {"symbols": ["AAPL"]}
        )

        assert len(result) == 1
        assert '"symbol": "AAPL"' in result[0].text
        mock_service.get_current_price.assert_called_once_with(["AAPL"])


@pytest.mark.asyncio
async def test_call_tool_price_history():
    from robin_stocks_mcp.server import call_tool

    with patch("robin_stocks_mcp.server.market_service") as mock_service:
        mock_candle = MagicMock()
        mock_candle.model_dump.return_value = {
            "timestamp": "2026-02-11T10:00:00Z",
            "open": 150.0,
            "high": 151.0,
            "low": 149.0,
            "close": 150.5,
            "volume": 1000000,
        }
        mock_service.get_price_history.return_value = [mock_candle]

        result = await call_tool(
            "robinhood.market.price_history",
            {"symbol": "AAPL", "interval": "day", "span": "year"},
        )

        assert len(result) == 1
        assert '"close": 150.5' in result[0].text


@pytest.mark.asyncio
async def test_call_tool_options_chain():
    from robin_stocks_mcp.server import call_tool

    with patch("robin_stocks_mcp.server.options_service") as mock_service:
        mock_contract = MagicMock()
        mock_contract.model_dump.return_value = {
            "symbol": "AAPL",
            "expiration": "2026-03-20",
            "strike": 150.0,
            "type": "call",
        }
        mock_service.get_options_chain.return_value = [mock_contract]

        result = await call_tool("robinhood.options.chain", {"symbol": "AAPL"})

        assert len(result) == 1
        assert '"symbol": "AAPL"' in result[0].text


@pytest.mark.asyncio
async def test_call_tool_portfolio_summary():
    from robin_stocks_mcp.server import call_tool

    with patch("robin_stocks_mcp.server.portfolio_service") as mock_service:
        mock_summary = MagicMock()
        mock_summary.model_dump.return_value = {
            "equity": 10000.50,
            "cash": 2500.0,
            "buying_power": 12500.0,
        }
        mock_service.get_portfolio_summary.return_value = mock_summary

        result = await call_tool("robinhood.portfolio.summary", {})

        assert len(result) == 1
        assert '"equity": 10000.5' in result[0].text


@pytest.mark.asyncio
async def test_call_tool_portfolio_positions():
    from robin_stocks_mcp.server import call_tool

    with patch("robin_stocks_mcp.server.portfolio_service") as mock_service:
        mock_position = MagicMock()
        mock_position.model_dump.return_value = {
            "symbol": "AAPL",
            "quantity": 100,
            "average_cost": 145.0,
        }
        mock_service.get_positions.return_value = [mock_position]

        result = await call_tool("robinhood.portfolio.positions", {})

        assert len(result) == 1
        assert '"symbol": "AAPL"' in result[0].text


@pytest.mark.asyncio
async def test_call_tool_watchlists():
    from robin_stocks_mcp.server import call_tool

    with patch("robin_stocks_mcp.server.watchlists_service") as mock_service:
        mock_watchlist = MagicMock()
        mock_watchlist.model_dump.return_value = {
            "id": "watchlist-123",
            "name": "My Watchlist",
            "symbols": ["AAPL", "GOOGL"],
        }
        mock_service.get_watchlists.return_value = [mock_watchlist]

        result = await call_tool("robinhood.watchlists.list", {})

        assert len(result) == 1
        assert '"name": "My Watchlist"' in result[0].text


@pytest.mark.asyncio
async def test_call_tool_news():
    from robin_stocks_mcp.server import call_tool

    with patch("robin_stocks_mcp.server.news_service") as mock_service:
        mock_news = MagicMock()
        mock_news.model_dump.return_value = {
            "id": "news-123",
            "headline": "Test News",
            "source": "TestSource",
        }
        mock_service.get_news.return_value = [mock_news]

        result = await call_tool("robinhood.news.latest", {"symbol": "AAPL"})

        assert len(result) == 1
        assert '"headline": "Test News"' in result[0].text


@pytest.mark.asyncio
async def test_call_tool_fundamentals():
    from robin_stocks_mcp.server import call_tool

    with patch("robin_stocks_mcp.server.fundamentals_service") as mock_service:
        mock_fundamentals = MagicMock()
        mock_fundamentals.model_dump.return_value = {
            "pe_ratio": 28.5,
            "market_cap": 2500000000000.0,
        }
        mock_service.get_fundamentals.return_value = mock_fundamentals

        result = await call_tool("robinhood.fundamentals.get", {"symbol": "AAPL"})

        assert len(result) == 1
        assert '"pe_ratio": 28.5' in result[0].text


@pytest.mark.asyncio
async def test_call_tool_auth_status_authenticated():
    from robin_stocks_mcp.server import call_tool

    with patch("robin_stocks_mcp.server.client") as mock_client:
        mock_client.ensure_session = MagicMock()

        result = await call_tool("robinhood.auth.status", {})

        assert len(result) == 1
        assert '"authenticated": true' in result[0].text


@pytest.mark.asyncio
async def test_call_tool_auth_status_not_authenticated():
    from robin_stocks_mcp.server import call_tool
    from robin_stocks_mcp.robinhood.errors import AuthRequiredError

    with patch("robin_stocks_mcp.server.client") as mock_client:
        mock_client.ensure_session.side_effect = AuthRequiredError("Not authenticated")

        result = await call_tool("robinhood.auth.status", {})

        assert len(result) == 1
        assert '"authenticated": false' in result[0].text


@pytest.mark.asyncio
async def test_call_tool_unknown_tool():
    from robin_stocks_mcp.server import call_tool

    result = await call_tool("unknown.tool", {})

    assert len(result) == 1
    assert "error" in result[0].text
    assert "Unknown tool" in result[0].text


@pytest.mark.asyncio
async def test_call_tool_handles_auth_required_error():
    from robin_stocks_mcp.server import call_tool
    from robin_stocks_mcp.robinhood.errors import AuthRequiredError

    with patch("robin_stocks_mcp.server.market_service") as mock_service:
        mock_service.get_current_price.side_effect = AuthRequiredError("Auth required")

        result = await call_tool(
            "robinhood.market.current_price", {"symbols": ["AAPL"]}
        )

        assert len(result) == 1
        assert "AUTH_REQUIRED" in result[0].text


@pytest.mark.asyncio
async def test_call_tool_handles_invalid_argument_error():
    from robin_stocks_mcp.server import call_tool
    from robin_stocks_mcp.robinhood.errors import InvalidArgumentError

    with patch("robin_stocks_mcp.server.market_service") as mock_service:
        mock_service.get_current_price.side_effect = InvalidArgumentError(
            "Invalid argument"
        )

        result = await call_tool("robinhood.market.current_price", {"symbols": []})

        assert len(result) == 1
        assert "INVALID_ARGUMENT" in result[0].text


@pytest.mark.asyncio
async def test_call_tool_handles_robinhood_api_error():
    from robin_stocks_mcp.server import call_tool
    from robin_stocks_mcp.robinhood.errors import RobinhoodAPIError

    with patch("robin_stocks_mcp.server.market_service") as mock_service:
        mock_service.get_current_price.side_effect = RobinhoodAPIError("API error")

        result = await call_tool(
            "robinhood.market.current_price", {"symbols": ["AAPL"]}
        )

        assert len(result) == 1
        assert "ROBINHOOD_ERROR" in result[0].text


@pytest.mark.asyncio
async def test_call_tool_handles_network_error():
    from robin_stocks_mcp.server import call_tool
    from robin_stocks_mcp.robinhood.errors import NetworkError

    with patch("robin_stocks_mcp.server.market_service") as mock_service:
        mock_service.get_current_price.side_effect = NetworkError("Network error")

        result = await call_tool(
            "robinhood.market.current_price", {"symbols": ["AAPL"]}
        )

        assert len(result) == 1
        assert "NETWORK_ERROR" in result[0].text


@pytest.mark.asyncio
async def test_call_tool_handles_generic_error():
    from robin_stocks_mcp.server import call_tool

    with patch("robin_stocks_mcp.server.market_service") as mock_service:
        mock_service.get_current_price.side_effect = Exception("Generic error")

        result = await call_tool(
            "robinhood.market.current_price", {"symbols": ["AAPL"]}
        )

        assert len(result) == 1
        assert "INTERNAL_ERROR" in result[0].text
