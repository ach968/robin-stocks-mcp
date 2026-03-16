# Robinhood Tools

A monorepo providing CLI and MCP access to the [robin-stocks](https://github.com/jmfernandes/robin_stocks) (unofficial) Robinhood API.

## Packages

| Package | Description |
|---------|-------------|
| `robinhood-core` | Shared library: client, models, services |
| `robinhood-cli` | CLI tool (`rh` command) for terminal access |
| `robinhood-mcp` | MCP server for AI assistants (Claude, OpenCode, etc.) |

## Quick Start

### CLI

```bash
# Clone and install globally
git clone https://github.com/ach968/robinhood-mcp.git
cd robinhood-mcp
uv tool install ./robinhood-cli

# Login (prompts for username/password)
rh login

# Use
rh price AAPL MSFT
rh quote TSLA
rh portfolio
rh positions
rh options-chain SPY --expiry 2026-06-20 --type call
rh history AAPL --interval day --span month
rh orders --type stock --since 2026-01-01
rh watchlists
rh news NVDA
rh fundamentals AMD
rh status
rh logout
```

All commands support `--json` for raw JSON output.

### MCP Server

Add to your OpenCode config (`~/.config/opencode/opencode.json`):

```json
{
  "mcp": {
    "robinhood": {
      "type": "local",
      "command": [
        "uvx",
        "--from", "git+https://github.com/ach968/robinhood-mcp.git",
        "robinhood-mcp",
        "--username", "your_username",
        "--password", "your_password"
      ],
      "enabled": true
    }
  }
}
```

See [robinhood-mcp/README.md](robinhood-mcp/README.md) for full MCP documentation.

## Development

```bash
# Clone
git clone https://github.com/ach968/robinhood-mcp.git
cd robinhood-mcp

# Install all packages
cd robinhood-core && uv pip install -e ".[dev]"
cd ../robinhood-cli && uv pip install -e ".[dev]"
cd ../robinhood-mcp && uv pip install -e ".[dev]"

# Run tests
cd robinhood-core && uv run pytest tests/ -v
cd ../robinhood-cli && uv run pytest tests/ -v
cd ../robinhood-mcp && uv run pytest tests/ -v
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `rh login` | Authenticate with Robinhood |
| `rh logout` | Clear saved session |
| `rh status` | Show authentication status |
| `rh price SYMBOLS...` | Current prices |
| `rh quote SYMBOLS...` | Detailed quotes with change |
| `rh history SYMBOL` | Historical OHLCV data |
| `rh portfolio` | Portfolio summary |
| `rh positions` | Open stock positions |
| `rh options-chain SYMBOL` | Options chain |
| `rh options-positions` | Open options positions |
| `rh watchlists` | List watchlists |
| `rh news SYMBOL` | Latest news |
| `rh fundamentals SYMBOL` | Company fundamentals |
| `rh orders` | Order history |

All commands accept `--json` for machine-readable output.

## MCP Tools

| Tool | Description |
|------|-------------|
| `robinhood.market.current_price` | Current price quotes |
| `robinhood.market.price_history` | Historical OHLCV data |
| `robinhood.market.quote` | Detailed quotes |
| `robinhood.options.chain` | Options chain |
| `robinhood.orders.history` | Order history |
| `robinhood.portfolio.summary` | Portfolio summary |
| `robinhood.portfolio.positions` | Current positions |
| `robinhood.watchlists.list` | Watchlists |
| `robinhood.news.latest` | Latest news |
| `robinhood.fundamentals.get` | Company fundamentals |
| `robinhood.auth.status` | Auth status |

## Architecture

```
robinhood-core/           # Shared library
├── robinhood_core/
│   ├── client.py         # RobinhoodClient (robin-stocks wrapper)
│   ├── errors.py         # Exception types
│   ├── models/           # Pydantic models
│   └── services/         # Business logic services

robinhood-cli/            # CLI tool
├── robinhood_cli/
│   ├── main.py           # Typer app entry point
│   ├── auth.py           # Session management
│   ├── output.py         # Rich formatting helpers
│   └── commands/         # Command modules

robinhood-mcp/            # MCP server
├── robin_stocks_mcp/
│   └── server.py         # MCP tool implementations
```

## Security Notes

- All tools are **read-only** — cannot place orders or modify accounts
- CLI stores session tokens in `~/.config/robinhood/` (pickle file + config)
- MCP accepts credentials via CLI args or environment variables
- Passwords and tokens are never logged

## Disclaimer

This project uses [robin-stocks](https://github.com/jmfernandes/robin_stocks), an unofficial Python library. It is not affiliated with or endorsed by Robinhood Markets, Inc. Use at your own risk.

## License

[MIT](LICENSE)
