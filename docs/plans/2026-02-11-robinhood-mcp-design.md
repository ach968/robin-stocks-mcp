# Robinhood MCP Server Design (2026-02-11)

## Summary
- Build a read-only MCP server around the robin_stocks Robinhood API.
- Use stdio transport with the official Python mcp SDK.
- Provide normalized domain models with stable fields and coerced types.
- Lazy auth on first tool call with optional session caching to disk.

## Goals
- Read-only market data, options, portfolio, watchlists, news, and fundamentals.
- Minimal, stable response schemas (no raw payload pass-through).
- Simple, predictable error surface for MCP clients.
- Authentication that works with an existing app-based biometric session.

## Non-goals
- Trading, order placement, or account mutations.
- Streaming/real-time updates.
- Rate limiting or automatic retries.
- Full schema coverage of every robin_stocks field.

## Architecture
The server is a thin domain-model adapter over robin_stocks using stdio MCP.
`server.py` is the entrypoint and registers tools. Tool handlers call service
functions that wrap robin_stocks calls and map results into normalized models.
Normalization happens in one place to keep schemas stable and consistent.

## Components and Files
- `server.py`: MCP server setup, tool registration, stdio transport.
- `robinhood/client.py`: session management and lazy authentication.
- `services/`: thin orchestration modules by domain.
  - `market_data.py`, `options.py`, `portfolio.py`, `watchlists.py`,
    `news.py`, `fundamentals.py`
- `models/`: dataclasses + coercion helpers for normalized outputs.

## Authentication and Session Management
Auth is lazy and session-first to align with app biometric workflows.

Flow:
1) Server starts; no login attempt is made.
2) Client checks optional session cache file on first tool call.
3) If valid, use it. If missing/expired, attempt login with env creds.
4) If Robinhood requires a challenge and MFA fallback is disabled, return
   `AUTH_REQUIRED` with guidance to refresh the session in the app.

Config:
- `RH_USERNAME`, `RH_PASSWORD`: required for login fallback.
- `RH_SESSION_PATH`: optional path for stored session tokens.
- `RH_EAGER_LOGIN=1`: optional startup login (default off).
- `RH_ALLOW_MFA=1`: enable MFA fallback (default off).

If MFA fallback is enabled, tool calls can include an optional `mfa_code`
parameter that is passed into login when needed.

## Tools and Domain Models (v0)
All responses are normalized with numeric coercion and ISO 8601 timestamps.

- `robinhood.market.current_price`
  - Input: `symbol` or `symbols[]`
  - Output: `Quote[]` (`symbol`, `last_price`, `bid`, `ask`, `timestamp`)

- `robinhood.market.price_history`
  - Input: `symbol`, `interval`, `span`, `bounds`
  - Output: `Candle[]` (`timestamp`, `open`, `high`, `low`, `close`, `volume`)

- `robinhood.market.quote`
  - Input: `symbol` or `symbols[]`
  - Output: `Quote[]` (same as above with optional extras like `prev_close`)

- `robinhood.options.chain`
  - Input: `symbol`, optional `expiration_date`
  - Output: `OptionContract[]` (`symbol`, `expiration`, `strike`, `type`,
    `bid`, `ask`, `open_interest`, `volume`)

- `robinhood.portfolio.summary`
  - Input: none
  - Output: `PortfolioSummary` (`equity`, `cash`, `buying_power`,
    `unrealized_pl`, `day_change`)

- `robinhood.portfolio.positions`
  - Input: optional `symbols[]`
  - Output: `Position[]` (`symbol`, `quantity`, `average_cost`,
    `market_value`, `unrealized_pl`)

- `robinhood.watchlists.list`
  - Input: none
  - Output: `Watchlist[]` (`id`, `name`, `symbols[]`)

- `robinhood.news.latest`
  - Input: `symbol` or none
  - Output: `NewsItem[]` (`id`, `headline`, `summary`, `source`, `url`,
    `published_at`)

- `robinhood.fundamentals.get`
  - Input: `symbol`
  - Output: `Fundamentals` (`market_cap`, `pe_ratio`, `dividend_yield`,
    `week_52_high`, `week_52_low`)

Optional read-only tool:
- `robinhood.auth.status`: reports whether cached session is present/valid.

## Data Flow
1) MCP tool call arrives in `server.py`.
2) Handler validates inputs and calls the domain service.
3) Service requests an authenticated client via `ensure_session()`.
4) Service calls robin_stocks, then maps raw payload into models.
5) Model is returned as the tool response.

## Error Handling
All errors are surfaced as structured MCP errors with codes:
- `AUTH_REQUIRED`: no valid session or challenge required.
- `INVALID_ARGUMENT`: bad input values or formats.
- `ROBINHOOD_ERROR`: API-level failures.
- `NETWORK_ERROR`: connectivity or timeout issues.
- `INTERNAL_ERROR`: unexpected exceptions.

Sensitive values (passwords, tokens) are never logged.

## Testing
- Unit tests for model coercion and schema mapping using fixture payloads.
- Input validation tests for tool parameter validation.
- Optional integration tests gated by `RH_INTEGRATION=1` and credentials.
- Tests confirm lazy auth behavior (no login until first tool call).

## Security and Privacy
- Read-only allow-list of robin_stocks functions.
- No write endpoints imported or exposed.
- Token cache file is optional and should be user-controlled.

## Future Work
- Pagination helpers for larger lists.
- Optional caching of market data for repeated queries.
- Expanded fundamentals and options greeks once v0 is stable.
