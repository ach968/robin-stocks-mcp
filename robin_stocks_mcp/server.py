#!/usr/bin/env python3
"""MCP server for Robinhood API."""

import argparse
import asyncio
import json
import logging
from typing import List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from robin_stocks_mcp.robinhood.client import RobinhoodClient
from robin_stocks_mcp.robinhood.errors import (
    AuthRequiredError,
    InvalidArgumentError,
    RobinhoodAPIError,
    NetworkError,
)
from robin_stocks_mcp.services import (
    FundamentalsService,
    NewsService,
    OptionsService,
    OrdersService,
    PortfolioService,
    WatchlistsService,
)
from robin_stocks_mcp.services.market_data import MarketDataService

# Module-level references initialized by _init_services() before any tool call.
# Using TYPE_CHECKING guard so the type checker sees the concrete types.
client: RobinhoodClient  # type: ignore[assignment]
market_service: MarketDataService  # type: ignore[assignment]
options_service: OptionsService  # type: ignore[assignment]
portfolio_service: PortfolioService  # type: ignore[assignment]
watchlists_service: WatchlistsService  # type: ignore[assignment]
news_service: NewsService  # type: ignore[assignment]
fundamentals_service: FundamentalsService  # type: ignore[assignment]
orders_service: OrdersService  # type: ignore[assignment]

logger = logging.getLogger(__name__)

# Create MCP server
mcp = Server("robinhood-mcp")


def _init_services(
    username: Optional[str] = None,
    password: Optional[str] = None,
    session_path: Optional[str] = None,
    allow_mfa: Optional[bool] = None,
):
    """Initialize client and services. Args override env vars."""
    global client, market_service, options_service, portfolio_service, watchlists_service, news_service, fundamentals_service, orders_service

    client = RobinhoodClient(
        username=username,
        password=password,
        session_path=session_path,
        allow_mfa=allow_mfa,
    )
    market_service = MarketDataService(client)
    options_service = OptionsService(client)
    portfolio_service = PortfolioService(client)
    watchlists_service = WatchlistsService(client)
    news_service = NewsService(client)
    fundamentals_service = FundamentalsService(client)
    orders_service = OrdersService(client)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse CLI arguments. Args take priority over env vars."""
    parser = argparse.ArgumentParser(
        description="Robinhood MCP Server - read-only access to Robinhood API"
    )
    parser.add_argument(
        "--username",
        type=str,
        default=None,
        help="Robinhood username (overrides RH_USERNAME env var)",
    )
    parser.add_argument(
        "--password",
        type=str,
        default=None,
        help="Robinhood password (overrides RH_PASSWORD env var)",
    )
    parser.add_argument(
        "--session-path",
        type=str,
        default=None,
        help="Path to session cache file (overrides RH_SESSION_PATH env var)",
    )
    parser.add_argument(
        "--allow-mfa",
        action="store_true",
        default=None,
        help="Enable MFA fallback (overrides RH_ALLOW_MFA env var)",
    )
    return parser.parse_args(argv)


@mcp.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools."""
    return [
        Tool(
            name="robinhood.market.current_price",
            description="Get current price quotes for one or more symbols",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbols": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Stock ticker symbols",
                    }
                },
                "required": ["symbols"],
            },
        ),
        Tool(
            name="robinhood.market.price_history",
            description="Get historical price data for a symbol",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol",
                    },
                    "interval": {
                        "type": "string",
                        "description": "Data interval: 5minute, 10minute, hour, day, week",
                        "default": "hour",
                    },
                    "span": {
                        "type": "string",
                        "description": "Time span: day, week, month, 3month, year, 5year",
                        "default": "week",
                    },
                    "bounds": {
                        "type": "string",
                        "description": "Price bounds: extended, trading, regular",
                        "default": "regular",
                    },
                },
                "required": ["symbol"],
            },
        ),
        Tool(
            name="robinhood.market.quote",
            description="Get detailed stock quote for one or more symbols. Returns current price, previous close, change amount, and change percent. Use this instead of current_price when you need change/percent data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbols": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Stock ticker symbols",
                    }
                },
                "required": ["symbols"],
            },
        ),
        Tool(
            name="robinhood.options.chain",
            description=(
                "Get options chain for a symbol. This tool has TWO data tiers depending on whether strike_price is provided:\n\n"
                "TIER 1 — Chain listing (strike_price OMITTED): Returns a list of option contracts near the money (±20%% of current price) "
                "with basic instrument data: strike, type (call/put), expiration. Does NOT include bid/ask, Greeks, or market data. "
                "This is fast — use it to browse available strikes.\n\n"
                "TIER 2 — Targeted lookup (strike_price PROVIDED): Returns 1-2 contracts with FULL market data including: "
                "bid/ask, mark price, last trade price, open interest, volume, implied volatility, all Greeks "
                "(delta, gamma, theta, vega, rho), and chance of profit (long/short). This is the ONLY way to get Greeks from Robinhood.\n\n"
                "RECOMMENDED WORKFLOW for agents:\n"
                "  Step 1: Call with just symbol (and optionally expiration_date + option_type) to see available strikes.\n"
                "  Step 2: Pick a strike from the results.\n"
                "  Step 3: Call again with symbol + expiration_date + strike_price (+ option_type) to get full Greeks and market data.\n\n"
                "IMPORTANT: If you need Greeks, bid/ask, or IV — you MUST provide strike_price. Without it you only get strike/type/expiration.\n"
                "NOTE: expiration_date defaults to nearest available expiration if omitted."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., 'AAPL', 'TSLA')",
                    },
                    "expiration_date": {
                        "type": "string",
                        "description": "Expiration date in YYYY-MM-DD format. If omitted, defaults to the nearest available expiration. Required for targeted Greek lookups.",
                    },
                    "option_type": {
                        "type": "string",
                        "description": "Filter by option type: 'call' or 'put'. If omitted, returns both calls and puts.",
                    },
                    "strike_price": {
                        "type": "string",
                        "description": "Specific strike price (e.g., '150.00'). CRITICAL: When provided, switches to targeted lookup mode which returns full market data including bid/ask, Greeks (delta/gamma/theta/vega/rho), IV, and profit probability. Without this, only basic strike/type/expiration data is returned.",
                    },
                },
                "required": ["symbol"],
            },
        ),
        Tool(
            name="robinhood.options.positions",
            description=(
                "Get all open option positions for the authenticated account. Returns each position with: "
                "underlying symbol, strike price, expiration date, option type (call/put), direction (long/short), "
                "quantity, and average cost basis. Does NOT include current Greeks or market data — use "
                "robinhood.options.chain with the position's strike_price to get live Greeks and pricing."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="robinhood.portfolio.summary",
            description="Get portfolio summary",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="robinhood.portfolio.positions",
            description="Get portfolio positions",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbols": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional filter by symbols",
                    }
                },
            },
        ),
        Tool(
            name="robinhood.watchlists.list",
            description="Get watchlists",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="robinhood.news.latest",
            description="Get latest news for a stock symbol",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol",
                    }
                },
                "required": ["symbol"],
            },
        ),
        Tool(
            name="robinhood.fundamentals.get",
            description="Get company fundamentals (market cap, P/E, dividend yield, 52-week range)",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol",
                    }
                },
                "required": ["symbol"],
            },
        ),
        Tool(
            name="robinhood.auth.status",
            description="Check authentication status",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="robinhood.orders.history",
            description="Get order history for stocks, options, and/or crypto. Returns past trades with execution details, prices, quantities, and timestamps.",
            inputSchema={
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "description": "Order type to retrieve: stock, option, crypto, or all (default: all)",
                        "default": "all",
                    },
                    "symbol": {
                        "type": "string",
                        "description": "Filter by stock ticker symbol (applies to stock and option orders only)",
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date filter in YYYY-MM-DD format. Returns orders from this date to now.",
                    },
                },
            },
        ),
    ]


@mcp.call_tool()
async def call_tool(name: str, arguments: dict) -> List[TextContent]:
    """Handle tool calls."""
    assert client is not None, "Services not initialized. Call _init_services() first."
    assert market_service is not None
    assert options_service is not None
    assert portfolio_service is not None
    assert watchlists_service is not None
    assert news_service is not None
    assert fundamentals_service is not None

    logger.debug("Tool called: %s", name)

    try:
        if name == "robinhood.market.current_price":
            symbols = arguments["symbols"]
            quotes = await asyncio.to_thread(
                market_service.get_current_price, symbols
            )
            return [
                TextContent(
                    type="text", text=json.dumps([q.model_dump() for q in quotes])
                )
            ]

        elif name == "robinhood.market.price_history":
            symbol = arguments["symbol"]
            interval = arguments.get("interval", "hour")
            span = arguments.get("span", "week")
            bounds = arguments.get("bounds", "regular")
            candles = await asyncio.to_thread(
                market_service.get_price_history,
                symbol,
                interval,
                span,
                bounds,
            )
            return [
                TextContent(
                    type="text", text=json.dumps([c.model_dump() for c in candles])
                )
            ]

        elif name == "robinhood.market.quote":
            symbols = arguments["symbols"]
            quotes = await asyncio.to_thread(
                market_service.get_current_price, symbols
            )
            return [
                TextContent(
                    type="text", text=json.dumps([q.model_dump() for q in quotes])
                )
            ]

        elif name == "robinhood.options.chain":
            symbol = arguments["symbol"]
            expiration_date = arguments.get("expiration_date")
            option_type = arguments.get("option_type")
            strike_price = arguments.get("strike_price")
            contracts = await asyncio.to_thread(
                options_service.get_options_chain,
                symbol,
                expiration_date,
                option_type,
                strike_price,
            )
            return [
                TextContent(
                    type="text", text=json.dumps([c.model_dump() for c in contracts])
                )
            ]

        elif name == "robinhood.options.positions":
            positions = await asyncio.to_thread(
                options_service.get_option_positions,
            )
            return [
                TextContent(
                    type="text", text=json.dumps([p.model_dump() for p in positions])
                )
            ]

        elif name == "robinhood.portfolio.summary":
            summary = portfolio_service.get_portfolio_summary()
            return [TextContent(type="text", text=json.dumps(summary.model_dump()))]

        elif name == "robinhood.portfolio.positions":
            symbols = arguments.get("symbols")
            positions = portfolio_service.get_positions(symbols)
            return [
                TextContent(
                    type="text", text=json.dumps([p.model_dump() for p in positions])
                )
            ]

        elif name == "robinhood.watchlists.list":
            watchlists = watchlists_service.get_watchlists()
            return [
                TextContent(
                    type="text", text=json.dumps([w.model_dump() for w in watchlists])
                )
            ]

        elif name == "robinhood.news.latest":
            symbol = arguments["symbol"]
            news = await asyncio.to_thread(news_service.get_news, symbol)
            return [
                TextContent(
                    type="text", text=json.dumps([n.model_dump() for n in news])
                )
            ]

        elif name == "robinhood.fundamentals.get":
            symbol = arguments["symbol"]
            fundamentals = await asyncio.to_thread(
                fundamentals_service.get_fundamentals, symbol
            )
            return [
                TextContent(
                    type="text", text=json.dumps(fundamentals.model_dump())
                )
            ]

        elif name == "robinhood.auth.status":
            try:
                client.ensure_session()
                return [
                    TextContent(type="text", text=json.dumps({"authenticated": True}))
                ]
            except AuthRequiredError:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {"authenticated": False, "error": "Authentication required"}
                        ),
                    )
                ]

        elif name == "robinhood.orders.history":
            order_type = arguments.get("type", "all")
            symbol = arguments.get("symbol")
            start_date = arguments.get("start_date")
            history = await asyncio.to_thread(
                orders_service.get_order_history,
                order_type,
                symbol,
                start_date,
            )
            return [
                TextContent(
                    type="text", text=json.dumps(history.model_dump())
                )
            ]

        else:
            return [
                TextContent(
                    type="text", text=json.dumps({"error": f"Unknown tool: {name}"})
                )
            ]

    except AuthRequiredError as e:
        logger.warning("Tool %s failed: AUTH_REQUIRED: %s", name, e)
        return [
            TextContent(type="text", text=json.dumps({"error": f"AUTH_REQUIRED: {e}"}))
        ]
    except InvalidArgumentError as e:
        logger.warning("Tool %s failed: INVALID_ARGUMENT: %s", name, e)
        return [
            TextContent(
                type="text", text=json.dumps({"error": f"INVALID_ARGUMENT: {e}"})
            )
        ]
    except RobinhoodAPIError as e:
        logger.warning("Tool %s failed: ROBINHOOD_ERROR: %s", name, e)
        return [
            TextContent(
                type="text", text=json.dumps({"error": f"ROBINHOOD_ERROR: {e}"})
            )
        ]
    except NetworkError as e:
        logger.warning("Tool %s failed: NETWORK_ERROR: %s", name, e)
        return [
            TextContent(type="text", text=json.dumps({"error": f"NETWORK_ERROR: {e}"}))
        ]
    except Exception as e:
        logger.warning("Tool %s failed: INTERNAL_ERROR: %s", name, e)
        return [
            TextContent(type="text", text=json.dumps({"error": f"INTERNAL_ERROR: {e}"}))
        ]


async def run_server():
    """Run the MCP server over stdio."""
    async with stdio_server() as (read_stream, write_stream):
        await mcp.run(read_stream, write_stream, mcp.create_initialization_options())


def main():
    """Entry point: parse args, init services, start server."""
    args = parse_args()
    _init_services(
        username=args.username,
        password=args.password,
        session_path=args.session_path,
        allow_mfa=args.allow_mfa,
    )
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
