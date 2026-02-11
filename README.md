# Robinhood MCP Server

A read-only MCP (Model Context Protocol) server wrapping the [robin-stocks](https://github.com/jmfernandes/robin_stocks) (unofficial) Robinhood API.

## Features

- **Read-only access**: Market data, options, portfolio, watchlists, news, and fundamentals
- **Normalized schemas**: Consistent, typed responses with numeric coercion and ISO 8601 timestamps
- **Biometric-friendly auth**: Works with app-based authentication flow (no MFA code needed)
- **Lazy authentication**: Authenticates on first tool call, not at startup
- **Session caching**: Persists sessions to disk via robin-stocks pickle files for faster reconnects

## Installation

```bash
git clone https://github.com/ach968/robin-stocks-mcp.git
cd robin-stocks-mcp
pip install -e ".[dev]"
```

## Configuration (mcp.json)

Add to your MCP client config (e.g. `mcp.json` or Claude Desktop settings):

```json
{
  "mcpServers": {
    "robinhood": {
      "command": "python",
      "args": [
        "-m", "robin_stocks_mcp",
        "--username", "your_robinhood_username",
        "--password", "your_robinhood_password",
        "--session-path", "/path/to/session/directory"
      ]
    }
  }
}
```

### CLI Arguments

| Arg | Env Fallback | Description |
|-----|-------------|-------------|
| `--username` | `RH_USERNAME` | Robinhood username |
| `--password` | `RH_PASSWORD` | Robinhood password |
| `--session-path` | `RH_SESSION_PATH` | Directory for session pickle file |
| `--allow-mfa` | `RH_ALLOW_MFA=1` | Enable MFA code fallback (off by default) |

CLI args take priority over environment variables. You can also pass credentials
via the `env` block in `mcp.json` if you prefer:

```json
{
  "mcpServers": {
    "robinhood": {
      "command": "python",
      "args": ["-m", "robin_stocks_mcp"],
      "env": {
        "RH_USERNAME": "your_username",
        "RH_PASSWORD": "your_password",
        "RH_SESSION_PATH": "/path/to/session/directory"
      }
    }
  }
}
```

> **Note:** `--session-path` specifies a **directory** where robin-stocks stores its
> `robinhood.pickle` session file, not a file path.

## Usage

Run the server directly:

```bash
python -m robin_stocks_mcp --username myuser --password mypass
```

Or via the installed entry point:

```bash
robinhood-mcp --username myuser --password mypass
```

## Available Tools

### Market Data
- `robinhood.market.current_price` - Get current price quotes for one or more symbols
- `robinhood.market.price_history` - Get historical OHLCV data (intervals: 5min, 10min, hour, day, week)
- `robinhood.market.quote` - Get detailed quotes with previous close and change percent

### Options
- `robinhood.options.chain` - Get options chain for a symbol (calls and puts with greeks)

### Portfolio
- `robinhood.portfolio.summary` - Portfolio equity, cash, buying power, and day change
- `robinhood.portfolio.positions` - Current positions with market value and unrealized P&L

### Watchlists
- `robinhood.watchlists.list` - List all watchlists with their symbols

### News
- `robinhood.news.latest` - Get latest news for a stock symbol (symbol required)

### Fundamentals
- `robinhood.fundamentals.get` - Company fundamentals (market cap, P/E, dividend yield, 52-week range)

### Auth
- `robinhood.auth.status` - Check whether the session is authenticated

## Authentication Flow

1. The server starts without attempting login
2. On first tool call, robin-stocks tries to restore a cached session from the pickle file
3. If the cached session is valid, it is used without any interaction
4. If no valid session exists, it attempts a fresh login with credentials
5. If Robinhood requires a challenge and MFA is disabled, it returns an `AUTH_REQUIRED` error
6. To resolve: approve the login in the Robinhood app, then retry the tool call

## Testing

Unit tests:
```bash
pytest tests/unit -v
```

Integration tests (requires credentials):
```bash
RH_INTEGRATION=1 pytest tests/integration -v
```

## Security Notes

- This server is **read-only** and cannot place orders or modify your account
- Credentials are passed via CLI args or environment variables
- Session tokens are cached as pickle files (optional, user-controlled path)
- Passwords and tokens are never logged

## Disclaimer

This project uses [robin-stocks](https://github.com/jmfernandes/robin_stocks), an unofficial Python library for interacting with the Robinhood API. It is not affiliated with, endorsed by, or connected to Robinhood Markets, Inc. in any way. The Robinhood API is not officially documented or supported for third-party use. Use this software at your own risk and discretion. API behavior may change without notice, which could cause unexpected breakage.

## License

[MIT](LICENSE)
