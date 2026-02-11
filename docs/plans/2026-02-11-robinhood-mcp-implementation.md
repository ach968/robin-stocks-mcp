# Robinhood MCP Server Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a read-only MCP server around the robin_stocks Robinhood API with normalized domain models.

**Architecture:** Thin domain-model adapter over robin_stocks using the official `mcp` Python SDK with stdio transport. Lazy authentication on first tool call with optional session caching.

**Tech Stack:** Python 3.11+, `mcp` (Python SDK), `robin-stocks`, `pydantic` for models, `pytest` for testing

---

## Setup Tasks

### Task 1: Project Structure and Dependencies

**Files:**
- Create: `requirements.txt`
- Modify: `pyproject.toml`
- Create: `.env.example`

**Step 1: Update pyproject.toml**

Add these dependencies to pyproject.toml:

```toml
[project]
name = "robin-stocks-mcp"
version = "0.1.0"
description = "MCP server for Robinhood API"
requires-python = ">=3.11"
dependencies = [
    "mcp>=1.0.0",
    "robin-stocks>=3.0.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]
```

**Step 2: Create requirements.txt**

```
mcp>=1.0.0
robin-stocks>=3.0.0
pydantic>=2.0.0
pytest>=7.0.0
pytest-asyncio>=0.21.0
```

**Step 3: Create .env.example**

```bash
RH_USERNAME=your_robinhood_username
RH_PASSWORD=your_robinhood_password
RH_SESSION_PATH=./.robinhood_session.json
RH_ALLOW_MFA=0
RH_EAGER_LOGIN=0
```

**Step 4: Install dependencies**

Run: `pip install -e ".[dev]"`

Expected: All packages install successfully

**Step 5: Create directory structure**

Run:
```bash
mkdir -p robin_stocks_mcp/models
mkdir -p robin_stocks_mcp/services
mkdir -p robin_stocks_mcp/robinhood
mkdir -p tests/unit
mkdir -p tests/integration
```

**Step 6: Commit**

```bash
git add pyproject.toml requirements.txt .env.example
mkdir -p robin_stocks_mcp/models robin_stocks_mcp/services robin_stocks_mcp/robinhood tests/unit tests/integration
git add robin_stocks_mcp/ tests/
git commit -m "chore: project structure and dependencies"
```

---

## Domain Model Tasks

### Task 2: Core Domain Models

**Files:**
- Create: `robin_stocks_mcp/models/__init__.py`
- Create: `robin_stocks_mcp/models/base.py`
- Create: `robin_stocks_mcp/models/market.py`
- Test: `tests/unit/test_models_market.py`

**Step 1: Write failing test**

```python
# tests/unit/test_models_market.py
import pytest
from robin_stocks_mcp.models.market import Quote, Candle
from datetime import datetime

def test_quote_creation():
    quote = Quote(
        symbol="AAPL",
        last_price=150.50,
        bid=150.45,
        ask=150.55,
        timestamp="2026-02-11T10:00:00Z"
    )
    assert quote.symbol == "AAPL"
    assert quote.last_price == 150.50
    
def test_candle_creation():
    candle = Candle(
        timestamp="2026-02-11T10:00:00Z",
        open=150.0,
        high=151.0,
        low=149.0,
        close=150.5,
        volume=1000000
    )
    assert candle.open == 150.0
    assert candle.volume == 1000000
```

**Step 2: Run test (should fail)**

Run: `pytest tests/unit/test_models_market.py -v`

Expected: ImportError - models don't exist

**Step 3: Implement models**

```python
# robin_stocks_mcp/models/__init__.py
from .market import Quote, Candle
from .options import OptionContract
from .portfolio import PortfolioSummary, Position
from .watchlists import Watchlist
from .news import NewsItem
from .fundamentals import Fundamentals

__all__ = [
    "Quote",
    "Candle",
    "OptionContract",
    "PortfolioSummary",
    "Position",
    "Watchlist",
    "NewsItem",
    "Fundamentals",
]
```

```python
# robin_stocks_mcp/models/base.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

def coerce_timestamp(ts: Optional[str]) -> Optional[str]:
    """Ensure timestamp is ISO 8601 format."""
    if not ts:
        return None
    # Parse and re-format to ensure consistency
    try:
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        return dt.isoformat().replace('+00:00', 'Z')
    except:
        return ts

def coerce_numeric(value) -> Optional[float]:
    """Coerce string/number to float."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def coerce_int(value) -> Optional[int]:
    """Coerce string/number to int."""
    if value is None:
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None
```

```python
# robin_stocks_mcp/models/market.py
from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime
from .base import coerce_numeric, coerce_timestamp

class Quote(BaseModel):
    symbol: str
    last_price: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    timestamp: str
    previous_close: Optional[float] = None
    change_percent: Optional[float] = None
    
    @field_validator('last_price', 'bid', 'ask', 'previous_close', 'change_percent', mode='before')
    @classmethod
    def validate_numeric(cls, v):
        return coerce_numeric(v)
    
    @field_validator('timestamp', mode='before')
    @classmethod
    def validate_timestamp(cls, v):
        return coerce_timestamp(v)

class Candle(BaseModel):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    
    @field_validator('open', 'high', 'low', 'close', mode='before')
    @classmethod
    def validate_numeric(cls, v):
        return coerce_numeric(v)
    
    @field_validator('volume', mode='before')
    @classmethod
    def validate_int(cls, v):
        return coerce_int(v)
    
    @field_validator('timestamp', mode='before')
    @classmethod
    def validate_timestamp(cls, v):
        return coerce_timestamp(v)
```

**Step 4: Run test (should pass)**

Run: `pytest tests/unit/test_models_market.py -v`

Expected: PASS

**Step 5: Commit**

```bash
git add robin_stocks_mcp/models/ tests/unit/test_models_market.py
git commit -m "feat: add core market data models"
```

---

### Task 3: Options and Portfolio Models

**Files:**
- Create: `robin_stocks_mcp/models/options.py`
- Create: `robin_stocks_mcp/models/portfolio.py`
- Test: `tests/unit/test_models_options.py`
- Test: `tests/unit/test_models_portfolio.py`

**Step 1: Write failing tests**

```python
# tests/unit/test_models_options.py
import pytest
from robin_stocks_mcp.models.options import OptionContract
from datetime import datetime

def test_option_contract_creation():
    contract = OptionContract(
        symbol="AAPL",
        expiration="2026-03-20",
        strike=150.0,
        type="call",
        bid=5.50,
        ask=5.75,
        open_interest=1000,
        volume=500
    )
    assert contract.symbol == "AAPL"
    assert contract.strike == 150.0
    assert contract.type == "call"
```

```python
# tests/unit/test_models_portfolio.py
import pytest
from robin_stocks_mcp.models.portfolio import PortfolioSummary, Position

def test_portfolio_summary_creation():
    summary = PortfolioSummary(
        equity=10000.50,
        cash=2500.0,
        buying_power=12500.0,
        unrealized_pl=500.25,
        day_change=25.50
    )
    assert summary.equity == 10000.50
    
def test_position_creation():
    position = Position(
        symbol="AAPL",
        quantity=100,
        average_cost=145.0,
        market_value=15050.0,
        unrealized_pl=500.0
    )
    assert position.symbol == "AAPL"
    assert position.quantity == 100
```

**Step 2: Run tests (should fail)**

Run: `pytest tests/unit/test_models_options.py tests/unit/test_models_portfolio.py -v`

Expected: ImportError

**Step 3: Implement models**

```python
# robin_stocks_mcp/models/options.py
from pydantic import BaseModel, field_validator
from typing import Optional, Literal
from .base import coerce_numeric, coerce_int

class OptionContract(BaseModel):
    symbol: str
    expiration: str
    strike: float
    type: Literal["call", "put"]
    bid: Optional[float] = None
    ask: Optional[float] = None
    open_interest: Optional[int] = None
    volume: Optional[int] = None
    
    @field_validator('strike', 'bid', 'ask', mode='before')
    @classmethod
    def validate_numeric(cls, v):
        return coerce_numeric(v)
    
    @field_validator('open_interest', 'volume', mode='before')
    @classmethod
    def validate_int(cls, v):
        return coerce_int(v)
```

```python
# robin_stocks_mcp/models/portfolio.py
from pydantic import BaseModel, field_validator
from typing import Optional
from .base import coerce_numeric

class PortfolioSummary(BaseModel):
    equity: float
    cash: float
    buying_power: float
    unrealized_pl: Optional[float] = None
    day_change: Optional[float] = None
    
    @field_validator('equity', 'cash', 'buying_power', 'unrealized_pl', 'day_change', mode='before')
    @classmethod
    def validate_numeric(cls, v):
        return coerce_numeric(v)

class Position(BaseModel):
    symbol: str
    quantity: int
    average_cost: float
    market_value: float
    unrealized_pl: Optional[float] = None
    
    @field_validator('average_cost', 'market_value', 'unrealized_pl', mode='before')
    @classmethod
    def validate_numeric(cls, v):
        return coerce_numeric(v)
    
    @field_validator('quantity', mode='before')
    @classmethod
    def validate_int(cls, v):
        return coerce_numeric(v)
```

**Step 4: Run tests (should pass)**

Run: `pytest tests/unit/test_models_options.py tests/unit/test_models_portfolio.py -v`

Expected: PASS

**Step 5: Commit**

```bash
git add robin_stocks_mcp/models/ tests/unit/
git commit -m "feat: add options and portfolio models"
```

---

### Task 4: Watchlists, News, and Fundamentals Models

**Files:**
- Create: `robin_stocks_mcp/models/watchlists.py`
- Create: `robin_stocks_mcp/models/news.py`
- Create: `robin_stocks_mcp/models/fundamentals.py`
- Test: `tests/unit/test_models_watchlists.py`
- Test: `tests/unit/test_models_news.py`
- Test: `tests/unit/test_models_fundamentals.py`

**Step 1: Write failing tests**

```python
# tests/unit/test_models_watchlists.py
from robin_stocks_mcp.models.watchlists import Watchlist

def test_watchlist_creation():
    watchlist = Watchlist(
        id="watchlist-123",
        name="My Watchlist",
        symbols=["AAPL", "GOOGL", "MSFT"]
    )
    assert watchlist.name == "My Watchlist"
    assert len(watchlist.symbols) == 3
```

```python
# tests/unit/test_models_news.py
from robin_stocks_mcp.models.news import NewsItem

def test_news_item_creation():
    item = NewsItem(
        id="news-123",
        headline="Apple releases new product",
        summary="Summary here",
        source="TechCrunch",
        url="https://techcrunch.com/article",
        published_at="2026-02-11T10:00:00Z"
    )
    assert item.headline == "Apple releases new product"
```

```python
# tests/unit/test_models_fundamentals.py
from robin_stocks_mcp.models.fundamentals import Fundamentals

def test_fundamentals_creation():
    fundamentals = Fundamentals(
        market_cap=2500000000000.0,
        pe_ratio=28.5,
        dividend_yield=0.005,
        week_52_high=200.0,
        week_52_low=140.0
    )
    assert fundamentals.pe_ratio == 28.5
```

**Step 2: Run tests (should fail)**

Run: `pytest tests/unit/test_models_watchlists.py tests/unit/test_models_news.py tests/unit/test_models_fundamentals.py -v`

Expected: ImportError

**Step 3: Implement models**

```python
# robin_stocks_mcp/models/watchlists.py
from pydantic import BaseModel
from typing import List

class Watchlist(BaseModel):
    id: str
    name: str
    symbols: List[str]
```

```python
# robin_stocks_mcp/models/news.py
from pydantic import BaseModel, field_validator
from typing import Optional
from .base import coerce_timestamp

class NewsItem(BaseModel):
    id: str
    headline: str
    summary: Optional[str] = None
    source: Optional[str] = None
    url: Optional[str] = None
    published_at: str
    
    @field_validator('published_at', mode='before')
    @classmethod
    def validate_timestamp(cls, v):
        return coerce_timestamp(v)
```

```python
# robin_stocks_mcp/models/fundamentals.py
from pydantic import BaseModel, field_validator
from typing import Optional
from .base import coerce_numeric

class Fundamentals(BaseModel):
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    
    @field_validator('*', mode='before')
    @classmethod
    def validate_numeric(cls, v):
        return coerce_numeric(v)
```

**Step 4: Run tests (should pass)**

Run: `pytest tests/unit/test_models_watchlists.py tests/unit/test_models_news.py tests/unit/test_models_fundamentals.py -v`

Expected: PASS

**Step 5: Commit**

```bash
git add robin_stocks_mcp/models/ tests/unit/
git commit -m "feat: add watchlists, news, and fundamentals models"
```

---

## Authentication Tasks

### Task 5: Robinhood Client with Lazy Authentication

**Files:**
- Create: `robin_stocks_mcp/robinhood/__init__.py`
- Create: `robin_stocks_mcp/robinhood/client.py`
- Create: `robin_stocks_mcp/robinhood/errors.py`
- Test: `tests/unit/test_robinhood_client.py`

**Step 1: Write failing test**

```python
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
```

**Step 2: Run test (should fail)**

Run: `pytest tests/unit/test_robinhood_client.py -v`

Expected: ImportError

**Step 3: Implement client**

```python
# robin_stocks_mcp/robinhood/errors.py
class RobinhoodError(Exception):
    """Base error for Robinhood operations."""
    pass

class AuthRequiredError(RobinhoodError):
    """Raised when authentication is required but unavailable."""
    pass

class InvalidArgumentError(RobinhoodError):
    """Raised when tool input is invalid."""
    pass

class RobinhoodAPIError(RobinhoodError):
    """Raised when Robinhood API returns an error."""
    pass

class NetworkError(RobinhoodError):
    """Raised when network operations fail."""
    pass
```

```python
# robin_stocks_mcp/robinhood/client.py
import os
import json
from typing import Optional
from pathlib import Path
import robin_stocks.robinhood as rh
from .errors import AuthRequiredError, RobinhoodAPIError, NetworkError

class RobinhoodClient:
    """Manages Robinhood authentication and session state."""
    
    def __init__(self):
        self._authenticated = False
        self._username: Optional[str] = None
        self._password: Optional[str] = None
        self._session_path: Optional[str] = None
        self._allow_mfa: bool = False
        self._load_config()
    
    def _load_config(self):
        """Load configuration from environment."""
        self._username = os.getenv('RH_USERNAME')
        self._password = os.getenv('RH_PASSWORD')
        self._session_path = os.getenv('RH_SESSION_PATH')
        self._allow_mfa = os.getenv('RH_ALLOW_MFA', '0') == '1'
    
    def _load_session(self) -> bool:
        """Load cached session if available."""
        if not self._session_path:
            return False
        
        session_file = Path(self._session_path)
        if not session_file.exists():
            return False
        
        try:
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            # Try to use the session token
            # robin_stocks stores session internally, we just check if it's valid
            return self._is_session_valid()
        except Exception:
            return False
    
    def _save_session(self):
        """Save current session to disk."""
        if not self._session_path:
            return
        
        try:
            session_file = Path(self._session_path)
            session_file.parent.mkdir(parents=True, exist_ok=True)
            # robin_stocks manages the session internally
            # We just track that we have one
            with open(session_file, 'w') as f:
                json.dump({'authenticated': True}, f)
        except Exception:
            pass  # Don't fail if we can't save session
    
    def _is_session_valid(self) -> bool:
        """Check if current session is valid."""
        try:
            # Try a simple API call that requires auth
            account = rh.load_account_profile()
            return account is not None
        except Exception:
            return False
    
    def ensure_session(self, mfa_code: Optional[str] = None) -> 'RobinhoodClient':
        """Ensure we have a valid session, authenticating if needed.
        
        Raises:
            AuthRequiredError: If authentication is required but not possible.
        """
        if self._authenticated and self._is_session_valid():
            return self
        
        # Try to load cached session
        if self._load_session() and self._is_session_valid():
            self._authenticated = True
            return self
        
        # Need to authenticate
        if not self._username or not self._password:
            raise AuthRequiredError(
                "Authentication required. Please set RH_USERNAME and RH_PASSWORD, "
                "or ensure a valid session cache exists. You may need to refresh "
                "your session in the Robinhood app."
            )
        
        try:
            login_result = rh.login(
                self._username,
                self._password,
                mfa_code=mfa_code if self._allow_mfa else None,
                store_session=True
            )
            
            if login_result:
                self._authenticated = True
                self._save_session()
                return self
            else:
                raise AuthRequiredError(
                    "Login failed. Please check your credentials or refresh "
                    "your session in the Robinhood app."
                )
        except Exception as e:
            if "challenge" in str(e).lower():
                raise AuthRequiredError(
                    "Authentication challenge required. Please refresh your "
                    "session in the Robinhood app, or enable MFA fallback with "
                    "RH_ALLOW_MFA=1 and provide mfa_code."
                )
            raise NetworkError(f"Failed to authenticate: {e}")
    
    def logout(self):
        """Clear session."""
        try:
            rh.logout()
        except Exception:
            pass
        self._authenticated = False
        if self._session_path:
            try:
                Path(self._session_path).unlink(missing_ok=True)
            except Exception:
                pass
```

```python
# robin_stocks_mcp/robinhood/__init__.py
from .client import RobinhoodClient
from .errors import (
    RobinhoodError,
    AuthRequiredError,
    InvalidArgumentError,
    RobinhoodAPIError,
    NetworkError,
)

__all__ = [
    "RobinhoodClient",
    "RobinhoodError",
    "AuthRequiredError",
    "InvalidArgumentError",
    "RobinhoodAPIError",
    "NetworkError",
]
```

**Step 4: Run test (should pass)**

Run: `pytest tests/unit/test_robinhood_client.py -v`

Expected: PASS

**Step 5: Commit**

```bash
git add robin_stocks_mcp/robinhood/ tests/unit/test_robinhood_client.py
git commit -m "feat: add robinhood client with lazy authentication"
```

---

## Service Layer Tasks

### Task 6: Market Data Service

**Files:**
- Create: `robin_stocks_mcp/services/__init__.py`
- Create: `robin_stocks_mcp/services/market_data.py`
- Test: `tests/unit/test_service_market_data.py`

**Step 1: Write failing test**

```python
# tests/unit/test_service_market_data.py
import pytest
from unittest.mock import MagicMock, patch
from robin_stocks_mcp.services.market_data import MarketDataService
from robin_stocks_mcp.robinhood.client import RobinhoodClient

def test_service_initialization():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = MarketDataService(mock_client)
    assert service.client == mock_client
```

**Step 2: Run test (should fail)**

Run: `pytest tests/unit/test_service_market_data.py -v`

Expected: ImportError

**Step 3: Implement service**

```python
# robin_stocks_mcp/services/__init__.py
from .market_data import MarketDataService
from .options import OptionsService
from .portfolio import PortfolioService
from .watchlists import WatchlistsService
from .news import NewsService
from .fundamentals import FundamentalsService

__all__ = [
    "MarketDataService",
    "OptionsService",
    "PortfolioService",
    "WatchlistsService",
    "NewsService",
    "FundamentalsService",
]
```

```python
# robin_stocks_mcp/services/market_data.py
from typing import List, Optional
import robin_stocks.robinhood as rh
from robin_stocks_mcp.models import Quote, Candle
from robin_stocks_mcp.robinhood.client import RobinhoodClient
from robin_stocks_mcp.robinhood.errors import InvalidArgumentError, RobinhoodAPIError

class MarketDataService:
    """Service for market data operations."""
    
    def __init__(self, client: RobinhoodClient):
        self.client = client
    
    def get_current_price(self, symbols: List[str]) -> List[Quote]:
        """Get current price quotes for symbols."""
        if not symbols:
            raise InvalidArgumentError("At least one symbol is required")
        
        self.client.ensure_session()
        
        try:
            # Handle single symbol vs list
            if len(symbols) == 1:
                data = rh.get_quotes(symbols[0])
            else:
                data = rh.get_quotes(symbols)
            
            if not data:
                return []
            
            # Ensure list format
            if not isinstance(data, list):
                data = [data]
            
            quotes = []
            for item in data:
                quote = Quote(
                    symbol=item.get('symbol', ''),
                    last_price=item.get('last_trade_price'),
                    bid=item.get('bid_price'),
                    ask=item.get('ask_price'),
                    timestamp=item.get('updated_at'),
                    previous_close=item.get('previous_close'),
                    change_percent=item.get('change_percent')
                )
                quotes.append(quote)
            
            return quotes
        except Exception as e:
            raise RobinhoodAPIError(f"Failed to fetch quotes: {e}")
    
    def get_price_history(
        self,
        symbol: str,
        interval: str = 'day',
        span: str = 'year',
        bounds: str = 'regular'
    ) -> List[Candle]:
        """Get historical price data for a symbol."""
        if not symbol:
            raise InvalidArgumentError("Symbol is required")
        
        # Validate inputs
        valid_intervals = ['5minute', '10minute', 'hour', 'day', 'week']
        valid_spans = ['day', 'week', 'month', '3month', 'year', '5year', 'all']
        valid_bounds = ['extended', 'trading', 'regular', '24_7']
        
        if interval not in valid_intervals:
            raise InvalidArgumentError(f"Invalid interval. Must be one of: {valid_intervals}")
        if span not in valid_spans:
            raise InvalidArgumentError(f"Invalid span. Must be one of: {valid_spans}")
        if bounds not in valid_bounds:
            raise InvalidArgumentError(f"Invalid bounds. Must be one of: {valid_bounds}")
        
        self.client.ensure_session()
        
        try:
            data = rh.get_stock_historicals(
                symbol,
                interval=interval,
                span=span,
                bounds=bounds
            )
            
            if not data:
                return []
            
            candles = []
            for item in data:
                candle = Candle(
                    timestamp=item.get('begins_at'),
                    open=item.get('open_price'),
                    high=item.get('high_price'),
                    low=item.get('low_price'),
                    close=item.get('close_price'),
                    volume=item.get('volume')
                )
                candles.append(candle)
            
            return candles
        except Exception as e:
            raise RobinhoodAPIError(f"Failed to fetch price history: {e}")
```

**Step 4: Run test (should pass)**

Run: `pytest tests/unit/test_service_market_data.py -v`

Expected: PASS

**Step 5: Commit**

```bash
git add robin_stocks_mcp/services/market_data.py tests/unit/test_service_market_data.py
git commit -m "feat: add market data service"
```

---

### Task 7: Options Service

**Files:**
- Create: `robin_stocks_mcp/services/options.py`
- Test: `tests/unit/test_service_options.py`

**Step 1: Write failing test**

```python
# tests/unit/test_service_options.py
import pytest
from unittest.mock import MagicMock
from robin_stocks_mcp.services.options import OptionsService
from robin_stocks_mcp.robinhood.client import RobinhoodClient

def test_service_initialization():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = OptionsService(mock_client)
    assert service.client == mock_client
```

**Step 2: Run test (should fail)**

Run: `pytest tests/unit/test_service_options.py -v`

Expected: ImportError

**Step 3: Implement service**

```python
# robin_stocks_mcp/services/options.py
from typing import List, Optional
import robin_stocks.robinhood as rh
from robin_stocks_mcp.models import OptionContract
from robin_stocks_mcp.robinhood.client import RobinhoodClient
from robin_stocks_mcp.robinhood.errors import InvalidArgumentError, RobinhoodAPIError

class OptionsService:
    """Service for options operations."""
    
    def __init__(self, client: RobinhoodClient):
        self.client = client
    
    def get_options_chain(
        self,
        symbol: str,
        expiration_date: Optional[str] = None
    ) -> List[OptionContract]:
        """Get options chain for a symbol."""
        if not symbol:
            raise InvalidArgumentError("Symbol is required")
        
        self.client.ensure_session()
        
        try:
            # Get available expiration dates if not specified
            if expiration_date:
                expirations = [expiration_date]
            else:
                chains = rh.get_chains(symbol)
                expirations = chains.get('expiration_dates', [])
                if not expirations:
                    return []
                # Use nearest expiration
                expirations = [expirations[0]]
            
            contracts = []
            for exp in expirations:
                options_data = rh.find_options_by_expiration(
                    symbol,
                    expirationDate=exp
                )
                
                for item in options_data:
                    contract = OptionContract(
                        symbol=item.get('chain_symbol', symbol),
                        expiration=exp,
                        strike=item.get('strike_price'),
                        type='call' if item.get('type') == 'call' else 'put',
                        bid=item.get('bid_price'),
                        ask=item.get('ask_price'),
                        open_interest=item.get('open_interest'),
                        volume=item.get('volume')
                    )
                    contracts.append(contract)
            
            return contracts
        except Exception as e:
            raise RobinhoodAPIError(f"Failed to fetch options chain: {e}")
```

**Step 4: Run test (should pass)**

Run: `pytest tests/unit/test_service_options.py -v`

Expected: PASS

**Step 5: Commit**

```bash
git add robin_stocks_mcp/services/options.py tests/unit/test_service_options.py
git commit -m "feat: add options service"
```

---

### Task 8: Portfolio Service

**Files:**
- Create: `robin_stocks_mcp/services/portfolio.py`
- Test: `tests/unit/test_service_portfolio.py`

**Step 1: Write failing test**

```python
# tests/unit/test_service_portfolio.py
import pytest
from unittest.mock import MagicMock
from robin_stocks_mcp.services.portfolio import PortfolioService
from robin_stocks_mcp.robinhood.client import RobinhoodClient

def test_service_initialization():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = PortfolioService(mock_client)
    assert service.client == mock_client
```

**Step 2: Run test (should fail)**

Run: `pytest tests/unit/test_service_portfolio.py -v`

Expected: ImportError

**Step 3: Implement service**

```python
# robin_stocks_mcp/services/portfolio.py
from typing import List, Optional
import robin_stocks.robinhood as rh
from robin_stocks_mcp.models import PortfolioSummary, Position
from robin_stocks_mcp.robinhood.client import RobinhoodClient
from robin_stocks_mcp.robinhood.errors import RobinhoodAPIError

class PortfolioService:
    """Service for portfolio operations."""
    
    def __init__(self, client: RobinhoodClient):
        self.client = client
    
    def get_portfolio_summary(self) -> PortfolioSummary:
        """Get portfolio summary."""
        self.client.ensure_session()
        
        try:
            account = rh.load_account_profile()
            
            return PortfolioSummary(
                equity=account.get('equity'),
                cash=account.get('cash'),
                buying_power=account.get('buying_power'),
                unrealized_pl=account.get('unsettled_debit'),
                day_change=account.get('portfolio_cash')
            )
        except Exception as e:
            raise RobinhoodAPIError(f"Failed to fetch portfolio: {e}")
    
    def get_positions(self, symbols: Optional[List[str]] = None) -> List[Position]:
        """Get portfolio positions, optionally filtered by symbols."""
        self.client.ensure_session()
        
        try:
            positions_data = rh.get_open_stock_positions()
            
            positions = []
            for item in positions_data:
                # Get symbol from instrument URL
                instrument = rh.get_instrument_by_url(item.get('instrument'))
                symbol = instrument.get('symbol') if instrument else None
                
                # Filter if symbols specified
                if symbols and symbol not in symbols:
                    continue
                
                position = Position(
                    symbol=symbol or 'UNKNOWN',
                    quantity=item.get('quantity'),
                    average_cost=item.get('average_buy_price'),
                    market_value=None,  # Would need quote lookup
                    unrealized_pl=None  # Would need calculation
                )
                positions.append(position)
            
            return positions
        except Exception as e:
            raise RobinhoodAPIError(f"Failed to fetch positions: {e}")
```

**Step 4: Run test (should pass)**

Run: `pytest tests/unit/test_service_portfolio.py -v`

Expected: PASS

**Step 5: Commit**

```bash
git add robin_stocks_mcp/services/portfolio.py tests/unit/test_service_portfolio.py
git commit -m "feat: add portfolio service"
```

---

### Task 9: Watchlists and News Services

**Files:**
- Create: `robin_stocks_mcp/services/watchlists.py`
- Create: `robin_stocks_mcp/services/news.py`
- Test: `tests/unit/test_service_watchlists.py`
- Test: `tests/unit/test_service_news.py`

**Step 1: Write failing tests**

```python
# tests/unit/test_service_watchlists.py
import pytest
from unittest.mock import MagicMock
from robin_stocks_mcp.services.watchlists import WatchlistsService
from robin_stocks_mcp.robinhood.client import RobinhoodClient

def test_service_initialization():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = WatchlistsService(mock_client)
    assert service.client == mock_client
```

```python
# tests/unit/test_service_news.py
import pytest
from unittest.mock import MagicMock
from robin_stocks_mcp.services.news import NewsService
from robin_stocks_mcp.robinhood.client import RobinhoodClient

def test_service_initialization():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = NewsService(mock_client)
    assert service.client == mock_client
```

**Step 2: Run tests (should fail)**

Run: `pytest tests/unit/test_service_watchlists.py tests/unit/test_service_news.py -v`

Expected: ImportError

**Step 3: Implement services**

```python
# robin_stocks_mcp/services/watchlists.py
from typing import List
import robin_stocks.robinhood as rh
from robin_stocks_mcp.models import Watchlist
from robin_stocks_mcp.robinhood.client import RobinhoodClient
from robin_stocks_mcp.robinhood.errors import RobinhoodAPIError

class WatchlistsService:
    """Service for watchlist operations."""
    
    def __init__(self, client: RobinhoodClient):
        self.client = client
    
    def get_watchlists(self) -> List[Watchlist]:
        """Get all watchlists."""
        self.client.ensure_session()
        
        try:
            watchlists_data = rh.get_all_watchlists()
            
            watchlists = []
            for item in watchlists_data:
                watchlist = Watchlist(
                    id=item.get('url', '').split('/')[-2] if item.get('url') else '',
                    name=item.get('name', ''),
                    symbols=[]  # Would need to fetch symbols separately
                )
                watchlists.append(watchlist)
            
            return watchlists
        except Exception as e:
            raise RobinhoodAPIError(f"Failed to fetch watchlists: {e}")
```

```python
# robin_stocks_mcp/services/news.py
from typing import List, Optional
import robin_stocks.robinhood as rh
from robin_stocks_mcp.models import NewsItem
from robin_stocks_mcp.robinhood.client import RobinhoodClient
from robin_stocks_mcp.robinhood.errors import RobinhoodAPIError

class NewsService:
    """Service for news operations."""
    
    def __init__(self, client: RobinhoodClient):
        self.client = client
    
    def get_news(self, symbol: Optional[str] = None) -> List[NewsItem]:
        """Get news for a symbol or general news."""
        self.client.ensure_session()
        
        try:
            if symbol:
                news_data = rh.get_news(symbol)
            else:
                # Get top news
                news_data = rh.get_top_news()
            
            if not news_data:
                return []
            
            items = []
            for item in news_data:
                news_item = NewsItem(
                    id=item.get('uuid', ''),
                    headline=item.get('title', ''),
                    summary=item.get('summary', ''),
                    source=item.get('source', ''),
                    url=item.get('url', ''),
                    published_at=item.get('published_at')
                )
                items.append(news_item)
            
            return items
        except Exception as e:
            raise RobinhoodAPIError(f"Failed to fetch news: {e}")
```

**Step 4: Run tests (should pass)**

Run: `pytest tests/unit/test_service_watchlists.py tests/unit/test_service_news.py -v`

Expected: PASS

**Step 5: Commit**

```bash
git add robin_stocks_mcp/services/watchlists.py robin_stocks_mcp/services/news.py tests/unit/
git commit -m "feat: add watchlists and news services"
```

---

### Task 10: Fundamentals Service

**Files:**
- Create: `robin_stocks_mcp/services/fundamentals.py`
- Test: `tests/unit/test_service_fundamentals.py`

**Step 1: Write failing test**

```python
# tests/unit/test_service_fundamentals.py
import pytest
from unittest.mock import MagicMock
from robin_stocks_mcp.services.fundamentals import FundamentalsService
from robin_stocks_mcp.robinhood.client import RobinhoodClient

def test_service_initialization():
    mock_client = MagicMock(spec=RobinhoodClient)
    service = FundamentalsService(mock_client)
    assert service.client == mock_client
```

**Step 2: Run test (should fail)**

Run: `pytest tests/unit/test_service_fundamentals.py -v`

Expected: ImportError

**Step 3: Implement service**

```python
# robin_stocks_mcp/services/fundamentals.py
from typing import Optional
import robin_stocks.robinhood as rh
from robin_stocks_mcp.models import Fundamentals
from robin_stocks_mcp.robinhood.client import RobinhoodClient
from robin_stocks_mcp.robinhood.errors import InvalidArgumentError, RobinhoodAPIError

class FundamentalsService:
    """Service for fundamentals operations."""
    
    def __init__(self, client: RobinhoodClient):
        self.client = client
    
    def get_fundamentals(self, symbol: str) -> Fundamentals:
        """Get fundamentals for a symbol."""
        if not symbol:
            raise InvalidArgumentError("Symbol is required")
        
        self.client.ensure_session()
        
        try:
            data = rh.get_fundamentals(symbol)
            
            if isinstance(data, list) and len(data) > 0:
                data = data[0]
            
            return Fundamentals(
                market_cap=data.get('market_cap'),
                pe_ratio=data.get('pe_ratio'),
                dividend_yield=data.get('dividend_yield'),
                week_52_high=data.get('high_52_weeks'),
                week_52_low=data.get('low_52_weeks')
            )
        except Exception as e:
            raise RobinhoodAPIError(f"Failed to fetch fundamentals: {e}")
```

**Step 4: Run test (should pass)**

Run: `pytest tests/unit/test_service_fundamentals.py -v`

Expected: PASS

**Step 5: Commit**

```bash
git add robin_stocks_mcp/services/fundamentals.py tests/unit/test_service_fundamentals.py
git commit -m "feat: add fundamentals service"
```

---

## MCP Server Tasks

### Task 11: MCP Server Setup and Tool Registration

**Files:**
- Create: `robin_stocks_mcp/server.py`
- Modify: Delete `main.py`
- Test: `tests/unit/test_server.py`

**Step 1: Write failing test**

```python
# tests/unit/test_server.py
import pytest
from unittest.mock import MagicMock, patch

def test_server_imports():
    from robin_stocks_mcp.server import mcp
    assert mcp is not None
```

**Step 2: Run test (should fail)**

Run: `pytest tests/unit/test_server.py -v`

Expected: ImportError

**Step 3: Implement server**

```python
# robin_stocks_mcp/server.py
#!/usr/bin/env python3
"""MCP server for Robinhood API."""

import asyncio
import os
from typing import List, Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ErrorCode, McpError

from robin_stocks_mcp.robinhood.client import RobinhoodClient
from robin_stocks_mcp.robinhood.errors import (
    RobinhoodError,
    AuthRequiredError,
    InvalidArgumentError,
    RobinhoodAPIError,
    NetworkError,
)
from robin_stocks_mcp.services import (
    MarketDataService,
    OptionsService,
    PortfolioService,
    WatchlistsService,
    NewsService,
    FundamentalsService,
)

# Initialize client and services
client = RobinhoodClient()
market_service = MarketDataService(client)
options_service = OptionsService(client)
portfolio_service = PortfolioService(client)
watchlists_service = WatchlistsService(client)
news_service = NewsService(client)
fundamentals_service = FundamentalsService(client)

# Create MCP server
mcp = Server("robinhood-mcp")

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
                        "description": "List of stock symbols (e.g., ['AAPL', 'GOOGL'])"
                    }
                },
                "required": ["symbols"]
            }
        ),
        Tool(
            name="robinhood.market.price_history",
            description="Get historical price data for a symbol",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol (e.g., 'AAPL')"
                    },
                    "interval": {
                        "type": "string",
                        "enum": ["5minute", "10minute", "hour", "day", "week"],
                        "description": "Data interval",
                        "default": "day"
                    },
                    "span": {
                        "type": "string",
                        "enum": ["day", "week", "month", "3month", "year", "5year", "all"],
                        "description": "Time span",
                        "default": "year"
                    },
                    "bounds": {
                        "type": "string",
                        "enum": ["extended", "trading", "regular", "24_7"],
                        "description": "Trading bounds",
                        "default": "regular"
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="robinhood.market.quote",
            description="Get detailed quotes for symbols",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbols": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of stock symbols"
                    }
                },
                "required": ["symbols"]
            }
        ),
        Tool(
            name="robinhood.options.chain",
            description="Get options chain for a symbol",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol"
                    },
                    "expiration_date": {
                        "type": "string",
                        "description": "Expiration date (YYYY-MM-DD). If not provided, uses nearest expiration.",
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="robinhood.portfolio.summary",
            description="Get portfolio summary",
            inputSchema={
                "type": "object",
                "properties": {}
            }
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
                        "description": "Optional filter by symbols"
                    }
                }
            }
        ),
        Tool(
            name="robinhood.watchlists.list",
            description="Get watchlists",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="robinhood.news.latest",
            description="Get latest news",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Optional symbol to filter news"
                    }
                }
            }
        ),
        Tool(
            name="robinhood.fundamentals.get",
            description="Get fundamentals for a symbol",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol"
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="robinhood.auth.status",
            description="Check authentication status",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
    ]

@mcp.call_tool()
async def call_tool(name: str, arguments: dict) -> List[TextContent]:
    """Handle tool calls."""
    import json
    
    try:
        if name == "robinhood.market.current_price":
            symbols = arguments.get("symbols", [])
            quotes = market_service.get_current_price(symbols)
            return [TextContent(type="text", text=json.dumps([q.model_dump() for q in quotes]))]
        
        elif name == "robinhood.market.price_history":
            symbol = arguments.get("symbol")
            interval = arguments.get("interval", "day")
            span = arguments.get("span", "year")
            bounds = arguments.get("bounds", "regular")
            candles = market_service.get_price_history(symbol, interval, span, bounds)
            return [TextContent(type="text", text=json.dumps([c.model_dump() for c in candles]))]
        
        elif name == "robinhood.market.quote":
            symbols = arguments.get("symbols", [])
            quotes = market_service.get_current_price(symbols)  # Same as current_price for now
            return [TextContent(type="text", text=json.dumps([q.model_dump() for q in quotes]))]
        
        elif name == "robinhood.options.chain":
            symbol = arguments.get("symbol")
            expiration_date = arguments.get("expiration_date")
            contracts = options_service.get_options_chain(symbol, expiration_date)
            return [TextContent(type="text", text=json.dumps([c.model_dump() for c in contracts]))]
        
        elif name == "robinhood.portfolio.summary":
            summary = portfolio_service.get_portfolio_summary()
            return [TextContent(type="text", text=json.dumps(summary.model_dump()))]
        
        elif name == "robinhood.portfolio.positions":
            symbols = arguments.get("symbols")
            positions = portfolio_service.get_positions(symbols)
            return [TextContent(type="text", text=json.dumps([p.model_dump() for p in positions]))]
        
        elif name == "robinhood.watchlists.list":
            watchlists = watchlists_service.get_watchlists()
            return [TextContent(type="text", text=json.dumps([w.model_dump() for w in watchlists]))]
        
        elif name == "robinhood.news.latest":
            symbol = arguments.get("symbol")
            news = news_service.get_news(symbol)
            return [TextContent(type="text", text=json.dumps([n.model_dump() for n in news]))]
        
        elif name == "robinhood.fundamentals.get":
            symbol = arguments.get("symbol")
            fundamentals = fundamentals_service.get_fundamentals(symbol)
            return [TextContent(type="text", text=json.dumps(fundamentals.model_dump()))]
        
        elif name == "robinhood.auth.status":
            try:
                client.ensure_session()
                return [TextContent(type="text", text=json.dumps({"authenticated": True}))]
            except AuthRequiredError:
                return [TextContent(type="text", text=json.dumps({"authenticated": False, "error": "Authentication required"}))]
        
        else:
            raise McpError(ErrorCode.MethodNotFound, f"Unknown tool: {name}")
    
    except AuthRequiredError as e:
        raise McpError(ErrorCode.InvalidRequest, f"AUTH_REQUIRED: {e}")
    except InvalidArgumentError as e:
        raise McpError(ErrorCode.InvalidParams, f"INVALID_ARGUMENT: {e}")
    except RobinhoodAPIError as e:
        raise McpError(ErrorCode.InternalError, f"ROBINHOOD_ERROR: {e}")
    except NetworkError as e:
        raise McpError(ErrorCode.InternalError, f"NETWORK_ERROR: {e}")
    except Exception as e:
        raise McpError(ErrorCode.InternalError, f"INTERNAL_ERROR: {e}")

async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await mcp.run(
            read_stream,
            write_stream,
            mcp.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
```

**Step 4: Update pyproject.toml entry point**

```toml
[project.scripts]
robinhood-mcp = "robin_stocks_mcp.server:main"
```

**Step 5: Delete main.py**

Run: `rm main.py`

**Step 6: Run test (should pass)**

Run: `pytest tests/unit/test_server.py -v`

Expected: PASS

**Step 7: Commit**

```bash
git add robin_stocks_mcp/server.py pyproject.toml
git rm main.py
git commit -m "feat: add MCP server with tool registration"
```

---

## Integration and Testing Tasks

### Task 12: Model Coercion Tests

**Files:**
- Create: `tests/unit/test_model_coercion.py`

**Step 1: Write comprehensive coercion tests**

```python
# tests/unit/test_model_coercion.py
import pytest
from robin_stocks_mcp.models.market import Quote, Candle
from robin_stocks_mcp.models.base import coerce_numeric, coerce_timestamp, coerce_int

def test_coerce_numeric_with_string():
    assert coerce_numeric("150.50") == 150.50
    
def test_coerce_numeric_with_float():
    assert coerce_numeric(150.50) == 150.50
    
def test_coerce_numeric_with_none():
    assert coerce_numeric(None) is None
    
def test_coerce_numeric_with_invalid():
    assert coerce_numeric("invalid") is None
    
def test_coerce_int_with_string():
    assert coerce_int("100") == 100
    
def test_coerce_int_with_float():
    assert coerce_int(100.5) == 100
    
def test_coerce_timestamp_with_iso():
    result = coerce_timestamp("2026-02-11T10:00:00Z")
    assert "2026-02-11" in result
    
def test_quote_accepts_string_prices():
    quote = Quote(
        symbol="AAPL",
        last_price="150.50",
        bid="150.45",
        ask="150.55",
        timestamp="2026-02-11T10:00:00Z"
    )
    assert quote.last_price == 150.50
    assert isinstance(quote.last_price, float)
    
def test_candle_accepts_string_values():
    candle = Candle(
        timestamp="2026-02-11T10:00:00Z",
        open="150.0",
        high="151.0",
        low="149.0",
        close="150.5",
        volume="1000000"
    )
    assert candle.open == 150.0
    assert candle.volume == 1000000
```

**Step 2: Run tests**

Run: `pytest tests/unit/test_model_coercion.py -v`

Expected: PASS

**Step 3: Commit**

```bash
git add tests/unit/test_model_coercion.py
git commit -m "test: add model coercion tests"
```

---

### Task 13: Service Integration Tests (Mocked)

**Files:**
- Create: `tests/unit/test_service_integration.py`

**Step 1: Write integration tests with mocked robin_stocks**

```python
# tests/unit/test_service_integration.py
import pytest
from unittest.mock import MagicMock, patch
from robin_stocks_mcp.services.market_data import MarketDataService
from robin_stocks_mcp.robinhood.client import RobinhoodClient

def test_market_service_with_mocked_data():
    mock_client = MagicMock(spec=RobinhoodClient)
    mock_client.ensure_session = MagicMock()
    
    service = MarketDataService(mock_client)
    
    # Mock robin_stocks
    with patch('robin_stocks_mcp.services.market_data.rh') as mock_rh:
        mock_rh.get_quotes.return_value = [
            {
                'symbol': 'AAPL',
                'last_trade_price': '150.50',
                'bid_price': '150.45',
                'ask_price': '150.55',
                'updated_at': '2026-02-11T10:00:00Z'
            }
        ]
        
        quotes = service.get_current_price(['AAPL'])
        
        assert len(quotes) == 1
        assert quotes[0].symbol == 'AAPL'
        assert quotes[0].last_price == 150.50
        mock_client.ensure_session.assert_called_once()
```

**Step 2: Run tests**

Run: `pytest tests/unit/test_service_integration.py -v`

Expected: PASS

**Step 3: Commit**

```bash
git add tests/unit/test_service_integration.py
git commit -m "test: add service integration tests with mocks"
```

---

### Task 14: End-to-End Smoke Test

**Files:**
- Create: `tests/integration/test_smoke.py`

**Step 1: Write smoke test**

```python
# tests/integration/test_smoke.py
import pytest
import os

# Skip if no credentials
pytestmark = pytest.mark.skipif(
    not os.getenv('RH_INTEGRATION'),
    reason="Integration tests disabled. Set RH_INTEGRATION=1 to run."
)

def test_client_can_load():
    """Verify client can be imported and initialized."""
    from robin_stocks_mcp.robinhood.client import RobinhoodClient
    client = RobinhoodClient()
    assert client is not None

def test_server_can_import():
    """Verify server module can be imported."""
    from robin_stocks_mcp.server import mcp
    assert mcp is not None
```

**Step 2: Run tests**

Run: `pytest tests/integration/test_smoke.py -v`

Expected: SKIP (unless RH_INTEGRATION=1)

**Step 3: Commit**

```bash
git add tests/integration/test_smoke.py
git commit -m "test: add integration smoke tests"
```

---

## Final Tasks

### Task 15: Update README

**Files:**
- Modify: `README.md`

**Step 1: Write comprehensive README**

```markdown
# Robinhood MCP Server

A read-only MCP (Model Context Protocol) server wrapping the robin_stocks Robinhood API.

## Features

- **Read-only access**: Market data, options, portfolio, watchlists, news, and fundamentals
- **Normalized schemas**: Consistent, typed responses with ISO 8601 timestamps
- **Biometric-friendly auth**: Works with app-based authentication flow
- **Lazy authentication**: Authenticates on first tool call, not at startup
- **Optional session caching**: Persist sessions to disk for faster reconnects

## Installation

```bash
pip install -e ".[dev]"
```

## Configuration

Create a `.env` file:

```bash
RH_USERNAME=your_robinhood_username
RH_PASSWORD=your_robinhood_password
RH_SESSION_PATH=./.robinhood_session.json  # Optional
RH_ALLOW_MFA=0  # Set to 1 to enable MFA fallback
```

## Usage

Run the server:

```bash
robinhood-mcp
```

Or directly:

```bash
python -m robin_stocks_mcp.server
```

## Available Tools

### Market Data
- `robinhood.market.current_price` - Get current prices
- `robinhood.market.price_history` - Get historical data
- `robinhood.market.quote` - Get detailed quotes

### Options
- `robinhood.options.chain` - Get options chain

### Portfolio
- `robinhood.portfolio.summary` - Portfolio summary
- `robinhood.portfolio.positions` - Current positions

### Watchlists & News
- `robinhood.watchlists.list` - List watchlists
- `robinhood.news.latest` - Latest news

### Fundamentals
- `robinhood.fundamentals.get` - Company fundamentals

### Auth
- `robinhood.auth.status` - Check authentication status

## Authentication Flow

1. The server starts without attempting login
2. On first tool call, it tries to use a cached session (if `RH_SESSION_PATH` is set)
3. If no valid session exists, it attempts login with credentials
4. If a challenge is required and MFA is disabled, it returns an `AUTH_REQUIRED` error
5. To authenticate using the app: refresh your session in the Robinhood app, then retry

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

- This server is read-only and cannot place orders
- Credentials are read from environment variables
- Session tokens can be cached to disk (optional)
- Sensitive values are never logged
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: update README with usage instructions"
```

---

### Task 16: Final Verification

**Step 1: Run all unit tests**

Run: `pytest tests/unit -v`

Expected: All PASS

**Step 2: Check code formatting**

Run: `black --check robin_stocks_mcp/ tests/`

If fails, run: `black robin_stocks_mcp/ tests/`

**Step 3: Run linter**

Run: `ruff check robin_stocks_mcp/ tests/`

Fix any issues.

**Step 4: Final commit**

```bash
git add .
git commit -m "style: format code with black and ruff"
```

---

## Summary

This implementation plan creates:
- 8 domain models with coercion and validation
- 1 authentication client with lazy auth
- 6 service modules
- 1 MCP server with 10 tools
- Comprehensive unit tests
- Integration test framework
- Full documentation

Total estimated time: 3-4 hours for a skilled developer following TDD.
