# AGENTS.md — Project Architecture & Development Guide

A comprehensive reference for tv-scraper's architecture, design patterns, and implementation details. This document consolidates artifacts from automated architecture exploration.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Installation & Testing](#installation--testing)
3. [Core Technologies](#core-technologies)
4. [Standardized Response Envelope](#standardized-response-envelope)
5. [WebSocket Architecture](#websocket-architecture)
6. [HTTP Scrapers](#http-scrapers)
7. [Streaming Methods](#streaming-methods)
8. [DataValidator Singleton](#datavalidator-singleton)
9. [Development Standards](#development-standards)
10. [Feature Matrix](#feature-matrix)
11. [Contributing](#contributing)

---

## Project Overview

**Purpose:** Python library for scraping financial data from TradingView.

**Key Features:**
- **Real-time streaming** via WebSocket (candles, forecast, price updates)
- **HTTP scraping** for social content (ideas, minds, news)
- **Type-safe code** with full type hints
- **Standardized error handling** across all scrapers
- **Optional export** to CSV/JSON formats

**Target Users:** Traders, quantitative analysts, financial data aggregators.

---

## Installation & Testing

### Install from Source
```bash
git clone https://github.com/yourusername/tv-scraper.git
cd tv-scraper
pip install -e .
```

### Run Tests
```bash
pytest tests/           # All tests
pytest tests/unit/      # Unit tests
pytest tests/live_api/  # Live TradingView API tests (live connection required)
pytest tests/integration/  # Cross-module integration tests
```

### Key Test Files
- `tests/unit/test_*.py` — Isolated component tests
- `tests/live_api/` — Tests requiring live TradingView connection
- `tests/integration/test_cross_module.py` — Multi-module workflows

---

## Core Technologies

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **WebSocket** | `websockets` (with custom framing) | Real-time streaming (candles, forecast) |
| **HTTP** | `requests` with `urllib3.util.retry` | Robust HTTP requests with auto-retries (`http.py`) |
| **Object Model**| `ScannerScraper` / `BaseScraper` | Centralized network/error handling & inheritance hierarchy |
| **Error Handling**| `@catch_errors` decorator | Automated metadata capture and standardized response envelopes |
| **Validation** | Module-level functions | Symbolic/exchange verification via `tv_scraper.core.validators` |
| **Data Mapping** | Hardcoded JSON mappings | Forecast key transformation, timeframe conversion |
| **Export** | CSV/JSON writers | Optional data persistence |
| **Parallelization** | `ThreadPoolExecutor` | Concurrent page scraping (ideas, minds) |

---

## Standardized Response Envelope

Every public scraper method returns an identical envelope structure, regardless of success or failure:

```python
{
    "status": "success" | "failed",
    "data": <scraper-specific data or None>,
    "metadata": {
        "exchange": str,
        "symbol": str,
        ...additional scraper-specific fields
    },
    "error": None | "error message"
}
```

### Design Principles

- **No exceptions raised** from public methods
- **All errors captured** in the `error` field
- **Status field** reflects operation outcome
- **Data field** set to `None` on failure
- **Metadata** preserved even on failure (for context)

### Example: Success Response

```python
{
    "status": "success",
    "data": [...],
    "metadata": {"exchange": "NASDAQ", "symbol": "AAPL", ...},
    "error": None
}
```

### Example: Error Response

```python
{
    "status": "failed",
    "data": None,
    "metadata": {"exchange": "NASDAQ", "symbol": "AAPL"},
    "error": "Symbol 'AAPL' not found on exchange 'NASDAQ'"
}
```

---

## Class Hierarchy & Core Architecture

To standardize network requests and error handling, all scrapers extend from central base classes:

### BaseScraper
The root class for all HTTP operations. Provides:
- **`self._request()`**: A unified wrapper around `requests` that handles timeouts, retries, and Captcha detection automatically.
- **`self._success_response()` / `self._error_response()`**: Factory methods for generating the standardized response envelope.
- **`self._export()`**: Handles auto-saving results to JSON / CSV.

### ScannerScraper
Extends `BaseScraper` for scrapers that interface directly with the `scanner.tradingview.com` API structure (e.g., `Fundamentals`, `Options`, `Technicals`, `Markets`, `Screener`, `MarketMovers`, `SymbolMarkets`, `Calendar`). Provides:
- Default `Content-Type: application/x-www-form-urlencoded` headers.
- Automatic payload formatting and response parsing for scanner tables.

### BaseStreamer
Extends `BaseScraper` for real-time WebSocket interactions. Provides:
- Connection bootstrapping via `StreamHandler`.
- JWT token authentication resolution natively baked into connection flows.

---

## WebSocket Architecture

### Connection Protocol

**URL:** `wss://data.tradingview.com/socket.io/websocket?from=chart%2F&type=chart`

**Message Framing:** Length-prefixed JSON protocol
```
Format: ~m~{length}~m~{JSON payload}
Length: Byte count of JSON string (UTF-8 encoded)
Payload: JSON-RPC style: {"m":"method_name","p":[arg1, arg2, ...]}
```

### Session Management

Each streaming operation creates **two concurrent sessions**:

| Session Type | Prefix | Purpose | Message Type |
|--------------|--------|---------|--------------|
| **Quote Session** | `qs_*` | Real-time price updates | `qsd` (Quote Session Data) |
| **Chart Session** | `cs_*` | OHLCV candles, indicators | `timescale_update`, `du` |

**Session ID Generation:**
```python
# Format: prefix + 12 random lowercase ASCII letters
# Example: qs_abcdefghijklm, cs_nopqrstuvwxyz
import secrets, string
def generate_session(prefix="qs_"):
    return prefix + "".join(secrets.choice(string.ascii_lowercase) for _ in range(12))
```

### Dual-Session Initialization Sequence

1. **set_auth_token** — Authorize with JWT (default: `"unauthorized_user_token"`)
2. **set_locale** — Set language/region (e.g., `["en", "US"]`)
3. **chart_create_session** — Create chart session for OHLCV
4. **quote_create_session** — Create quote session for prices
5. **quote_set_fields** — Subscribe to 24 price fields (bid, ask, volume, etc.)
6. **quote_hibernate_all** — Ready to receive updates

### Message Types Received

| Type | Session | Content | Frequency |
|------|---------|---------|-----------|
| **qsd** | Quote | Last price, bid/ask, spreads, volume | Per price update (~1/sec) |
| **timescale_update** | Chart | OHLCV candles for subscribed timeframe | Per candle close |
| **du** | Chart | Indicator value updates (RSI, MACD, etc.) | Real-time per update |
| **~h~** | Server | Keep-alive heartbeat | ~Every 30 seconds |

### Connection Optimization

| Parameter | Value | Purpose |
|-----------|-------|---------|
| **TCP_NODELAY** | `socket.TCP_NODELAY = 1` | Disables Nagle's algorithm → immediate packet transmission |
| **Socket Timeout** | 10 seconds | Prevents indefinite hangs on socket read |
| **Multithread Mode** | `enable_multithread=True` | Thread-safe concurrent send/receive |
| **User-Agent** | Chrome 107 | Mimics browser to avoid blocking |

### Heartbeat Handling

**Pattern Recognition:** `~m~\d+~m~~h~\d+$`

**Response:** Echo identical heartbeat back to server (automatically handled by `StreamHandler.receive_packets()`)

---

## HTTP Scrapers

### Ideas Scraper

**Source:** `tv_scraper/scrapers/social/ideas.py`
Extends `BaseScraper`.

**Endpoint:** `https://www.tradingview.com/symbols/{EXCHANGE}-{SYMBOL}/ideas/page-{N}/`

**Method Signature:**
```python
def get_ideas(
    exchange: str,
    symbol: str,
    start_page: int = 1,
    end_page: int = 1,
    sort_by: str = "popular"  # "popular" or "recent"
) -> dict[str, Any]
```

**Query Parameters:**
- `component-data-only=1` (tells API to return JSON only)
- `sort=recent` (only if sort_by="recent")

**Data Extraction:**
```
1. HTTP GET to endpoint
2. Parse JSON: response.json()["data"]["ideas"]["data"]["items"]
3. Map each item via _map_idea() static method
4. Concurrent page scraping: ThreadPoolExecutor(max_workers=3)
```

**Output Fields (per idea):**
```python
{
    "title": str,                    # Idea name
    "description": str,              # Full description
    "preview_image": list,           # Logo URLs
    "chart_url": str,                # Link to idea chart
    "comments_count": int,
    "views_count": int,
    "author": str,                   # Username
    "likes_count": int,
    "timestamp": int                 # Unix timestamp
}
```

**Error Detection:**
- Captcha: `"<title>Captcha Challenge</title>"` in HTML
- HTTP errors: Non-200 status codes
- Validation: DataValidator checks symbol/exchange

### Minds Scraper

**Source:** `tv_scraper/scrapers/social/minds.py`

**Endpoint:** `https://www.tradingview.com/api/v1/minds/`

**Method Signature:**
```python
def get_minds(
    exchange: str,
    symbol: str,
    limit: int | None = None
) -> dict[str, Any]
```

**Query Parameters:**
- `symbol={EXCHANGE}:{SYMBOL}` (colon-separated)
- `c={cursor}` (pagination cursor, only for subsequent pages)

**Data Extraction:**
```
1. HTTP GET to endpoint
2. Parse JSON: response.json()["results"]
3. Extract cursor from "next" field for pagination
4. Continue until limit reached or no next cursor
5. Client-side limit trimming: parsed_data[:limit]
```

**Output Fields (per mind):**
```python
{
    "text": str,                          # Idea text
    "url": str,                           # Link to idea
    "author": {
        "username": str,
        "profile_url": str,               # Constructed URL
        "is_broker": bool                 # Broker flag
    },
    "created": str,                       # ISO 8601, formatted as "YYYY-MM-DD HH:MM:SS"
    "total_likes": int,
    "total_comments": int
}
```

**Pagination:** Cursor-based (incremental loops)

### News Scraper

**Source:** `tv_scraper/scrapers/social/news.py`

**Endpoints:**
- **Headlines:** `https://news-headlines.tradingview.com/v2/view/headlines/symbol`
- **Story Content:** `https://news-mediator.tradingview.com/public/news/v1/story`

**Method Signatures:**
```python
def get_news_headlines(
    exchange: str,
    symbol: str,
    provider: str | None = None,
    area: str | None = None,
    sort_by: str = "latest",         # "latest", "oldest", "most_urgent", "least_urgent"
    section: str = "all",            # "all", "esg", "press_release", "financial_statement"
    language: str = "en"
) -> dict[str, Any]

def get_news_content(
    story_id: str,
    language: str = "en"
) -> dict[str, Any]
```

**Headlines Query Parameters:**
- `client=web`, `lang={lang}`, `area={area}`, `provider={provider}`, `section={section}`
- `streaming` (key-only parameter)
- `symbol={EXCHANGE}:{SYMBOL}`

**Story Query Parameters:**
- `id={story_id}` (e.g., `tag:reuters.com,2026:newsml_L4N3Z9104:0`)
- `lang={lang}`, `user_prostatus=non_pro`

**Headline Extraction:**
```
1. HTTP GET to headlines endpoint
2. Parse JSON: response.json()["items"]
3. Extract: id, title, shortDescription, published, storyPath
4. Client-side sort by: latest/oldest/most_urgent/least_urgent
```

**Story Parsing (Complex):**
```
1. HTTP GET to story endpoint with story_id
2. Recursively parse ast_description.children (AST traversal)
3. Extract paragraph nodes (type="p")
4. Merge text from paragraphs with \n separator
```

**Headline Output Fields:**
```python
{
    "id": str,                          # Story ID for get_news_content()
    "title": str,
    "shortDescription": str,
    "published": int,                   # Unix timestamp
    "storyPath": str                    # Always starts with "/"
}
```

**Story Output Fields:**
```python
{
    "title": str,
    "description": str,                 # Merged AST paragraphs
    "published": int,
    "storyPath": str
}
```

**Validation:**
- Symbol/exchange: DataValidator
- sort_by: Must be in `{"latest", "oldest", "most_urgent", "least_urgent"}`
- section: Must be in `{"all", "esg", "press_release", "financial_statement"}`
- language: Validated against `_languages` dict
- provider: Validated against `_news_providers` list
- area: Validated against `_areas` dict keys

---

## Streaming Methods

### Streamer.get_candles()

**Source:** `tv_scraper/streaming/streamer.py`

**Method Signature:**
```python
def get_candles(
    self,
    exchange: str,
    symbol: str,
    timeframe: str = "1m",
    numb_candles: int = 10,
    indicators: list[tuple[str, str]] | None = None
) -> dict[str, Any]
```

**Supported Timeframes:**
```
"1m", "5m", "15m", "30m", "1h", "2h", "4h", "1d", "1w", "1M"
```

**Timeframe Mapping to TradingView Values:**
```python
"1m" → "1", "5m" → "5", "15m" → "15", "30m" → "30"
"1h" → "60", "2h" → "120", "4h" → "240"
"1d" → "1D", "1w" → "1W", "1M" → "1M"
```

**WebSocket Subscription Flow:**
```
1. Create quote + chart sessions (via _add_symbol_to_sessions)
2. Send subscribe commands:
   - quote_add_symbols: Real-time price updates
   - resolve_symbol: Symbol resolution for chart
   - create_series: OHLCV data for timeframe
   - quote_fast_symbols: Fast price quotes
3. Receive timescale_update packets → OHLCV
4. Receive du packets → Indicator values
5. Exit when: (len(ohlcv) >= numb_candles AND indicators ready) OR timeout
```

**Message Filtering:**
| Type | Use | Ignore |
|------|-----|--------|
| `timescale_update` | Extract OHLCV | — |
| `du` | Extract indicators | — |
| `qsd` | — | Not used for historical |
| `~h~` | — | Auto-echoed |

**Data Extraction Logic:**
```python
# OHLCV from p[1].sds_1.s array:
{
    "index": entry["i"],
    "timestamp": entry["v"][0],        # Unix ms
    "open": entry["v"][1],
    "high": entry["v"][2],
    "low": entry["v"][3],
    "close": entry["v"][4],
    "volume": entry["v"][5]
}

# Indicators from p[1].st[N] arrays:
{
    "index": item["i"],
    "timestamp": item["v"][0],
    "0": item["v"][1],                 # Indicator output 1
    "1": item["v"][2]                  # Indicator output 2
}
```

**Stop Conditions:**
```
1. OHLCV received >= numb_candles AND
2. (Indicators ready OR no indicators requested)
3. OR timeout after 15 packets
```

**Output Structure:**
```python
{
    "status": "success",
    "data": {
        "ohlcv": [
            {
                "index": int,
                "timestamp": int,
                "open": float,
                "high": float,
                "low": float,
                "close": float,
                "volume": float
            }
        ],
        "indicators": {
            "STD;RSI": [
                {"index": int, "timestamp": int, "0": float, ...}
            ]
        }
    },
    "metadata": {
        "exchange": str,
        "symbol": str,
        "timeframe": str,
        "numb_candles": int
    },
    "error": None
}
```

### Streamer.get_forecast()

**Source:** `tv_scraper/streaming/streamer.py`

**Method Signature:**
```python
def get_forecast(
    self,
    exchange: str,
    symbol: str
) -> dict[str, Any]
```

**Validation Flow:**
```
1. Verify symbol/exchange exists (offline check)
2. HTTP GET to TradingView scanner API:
   https://scanner.tradingview.com/symbol?symbol={EXCHANGE}:{SYMBOL}&fields=market&no_404=false
3. Check response: type=="stock"
4. If non-stock: return error "Found non-stock symbol..."
5. Continue to WebSocket only if stock verified
```

**WebSocket Subscription:**
```
1. Create quote session
2. Send 5 subscribe/request commands (standard format)
3. Capture qsd packets only (incremental snapshots)
4. Merge snapshots via _merge_snapshot logic
```

**Key Mapping:**
```python
# TradingView source keys → tv-scraper output keys
{
    "earnings_fy_h": "yearly_eps_data",
    "earnings_ttm": "trailing_eps_data",
    # ... 8 more forecast mappings (bidirectional)
}

# Total: 10 required keys for success
```

**Stop Conditions:**
```
1. All 10 required keys found in snapshot, OR
2. 15 packets received (whichever first)
3. On timeout: Log warning with found_output_keys list
```

**Output Structure (Success):**
```python
{
    "status": "success",
    "data": {
        "yearly_eps_data": float,
        "trailing_eps_data": float,
        # ... 8 more fields
    },
    "metadata": {
        "exchange": str,
        "symbol": str
    },
    "error": None
}
```

**Output Structure (Partial/Timeout):**
```python
{
    "status": "failed",
    "data": <partial dict with found keys>,
    "metadata": {...},
    "error": "Timeout after 15 packets. Missing keys: ['key1', 'key2', ...]"
}
```

**Output Structure (Non-Stock):**
```python
{
    "status": "failed",
    "data": None,
    "metadata": {"exchange": str, "symbol": str},
    "error": "Found non-stock symbol (type=crypto). Forecast only available for stocks."
}
```

### StreamHandler Core Implementation

**Source:** `tv_scraper/streaming/stream_handler.py`

**Core Methods:**

| Method | Purpose | Returns |
|--------|---------|---------|
| `generate_session(prefix="qs_")` | Create unique session ID | `"qs_abcdefghijklm"` |
| `create_message(method, params)` | Build JSON-RPC message | `{"m":method, "p":params}` |
| `prepend_header(json_str)` | Add length prefix | `"~m~53~m~{json}"` |
| `send_message(msg)` | Transmit via WebSocket | None (logs errors) |
| `receive_packets()` | Generator yields JSON packets | Iterator[dict] |

**Packet Reception Logic:**
```
1. Receive bytes from WebSocket
2. If heartbeat (~h~ pattern): echo back, continue
3. If multiplexed: split via regex ~m~\d+~m~
4. Parse each part as JSON
5. Yield valid packets, skip invalid fragments
```

**Error Handling:**
- `WebSocketConnectionClosedException` → Log, break
- `TimeoutError` → Continue (non-fatal)
- `OSError/ConnectionError` → Log, break
- Always close socket in `finally` block

---

## Validation & Error Architecture

### @catch_errors Decorator
The primary mechanism for standardizing responses. Every public scraper method is decorated with `@catch_errors`, which:
1. **Captures Metadata**: Uses `inspect.signature` to automatically bind all function arguments (e.g., `symbol`, `exchange`, `limit`) into the response's `metadata` field.
2. **Standardizes Envelopes**: Wraps the function's return value in a `success` envelope or catches `ValidationError` / network exceptions to return a `failed` envelope.
3. **Eliminates Boilerplate**: Removes the need for manual `try/except` blocks and manual metadata dictionary construction in every method.

### DataValidator & Module Functions
Validation logic is centralized in `tv_scraper/core/validators.py`. While a `DataValidator` singleton exists internally to manage data loading, developers should use the exposed **module-level functions** for direct validation:

| Function | Purpose |
|----------|---------|
| `verify_symbol_exchange(exc, sym)` | Live check against TradingView for symbol existence. |
| `verify_options_symbol(exc, sym)` | Specifically verifies if a symbol has an options market. |
| `validate_exchange(exc)` | Offline check against known exchange list. |
| `validate_timeframe(tf)` | Validates TradingView-compatible timeframe strings. |
| `validate_choice(name, val, choices)`| Generic validator for string literal choices. |
| `validate_range(name, val, min, max)` | Generic numeric range validator. |
| `validate_fields(fields, allowed)` | Validates a list of requested data fields. |

**Design Rule:** Public methods should perform validation at the very beginning by calling these functions. Any `ValidationError` raised will be automatically caught by `@catch_errors` and formatted into a standardized error response.

---

**Source:** `tv_scraper/core/validators.py`

**Pattern:** Thread-unsafe singleton with lazy initialization

**Initialization:**
```python
# First instantiation loads 6 JSON files from tv_scraper/data/validators/:
_exchanges.json
_indicators.json
_timeframes.json
_languages.json
_areas.json
_news_providers.json
```

**Cached Data Structure:**
```python
_instance: Optional["DataValidator"] = None

def __new__(cls) -> "DataValidator":
    if cls._instance is None:
        cls._instance = super().__new__(cls)
        cls._instance._load_data()
    return cls._instance
```

### Validation Methods

#### Exchange Validation: `validate_exchange(exchange: str) -> bool`

**Type:** Offline check

**Logic:**
```python
1. Case-insensitive match: exchange.upper() in [e.upper() for e in self._exchanges]
2. On failure: Use difflib.get_close_matches(cutoff=0.6, n=5) for suggestions
3. Return sample of valid exchanges in error message
```

**Example:**
```python
try:
    validator.validate_exchange("NASDQ")  # Typo
except ValidationError as e:
    # "Invalid exchange: 'NASDQ'. Did you mean: 'NASDAQ'? Valid exchanges: NYSE, NASDAQ, ..."
```

#### Symbol Validation: `validate_symbol(exchange: str, symbol: str) -> bool`

**Type:** Offline check

**Logic:**
```python
1. isinstance(symbol, str)
2. symbol.strip() is not empty
3. No special character validation
```

#### Symbol-Exchange Verification: `verify_symbol_exchange(exchange: str, symbol: str, retries: int = 2) -> bool`

**Type:** Two-stage (offline + online)

**Stage 1 - Offline:**
```python
1. Call validate_exchange()
2. Call validate_symbol()
3. Return if offline checks fail
```

**Stage 2 - Online (HTTP):**
```python
# HTTP GET to TradingView scanner API:
https://scanner.tradingview.com/symbol?symbol={EXCHANGE}%3A{SYMBOL}&fields=market&no_404=false

# On 404: Raise ValidationError("Symbol '{symbol}' not found on exchange '{exchange}'")
# On network error: Retry up to retries times, timeout 5s per request
# On other HTTP error: Raise ValidationError with status code in message
```

**Retry Behavior:**
```python
for attempt in range(retries):
    try:
        response = requests.get(url, timeout=5)
    except requests.RequestException as e:
        if attempt == retries - 1:
            raise ValidationError(f"Could not verify after {retries} attempt(s): {e}")
        continue
```

#### Indicator Validation: `validate_indicators(indicators: list[str]) -> bool`

**Type:** Offline check

**Logic:**
```python
1. List is non-empty
2. Each indicator in self._indicators
3. Use difflib suggestions on first invalid indicator
```

### Data Getter Methods

All return **shallow copies** to prevent external mutation:

```python
get_exchanges() → list[str]
get_indicators() → list[str]
get_timeframes() → dict[str, Any]
get_news_providers() → list[str]
get_languages() → dict[str, str]
get_areas() → dict[str, str]
```

### Reset for Testing

```python
DataValidator.reset()  # Sets _instance = None for fresh reload in tests
```

---

## Development Standards

### Code Style
- **Type Hints:** All functions typed (params and return values)
- **Docstrings:** Google-style docstrings required
- **Naming:** `snake_case` for functions/variables, `PascalCase` for classes
- **Imports:** Absolute imports preferred, relative only within package

### Logging
- Use `logger.info()`, `logger.warning()`, `logger.error()` from module logger
- Include context: symbol, exchange, page number, operation
- Never log sensitive data (tokens, cookies)

### Error Handling
- Catch specific exceptions, not `Exception`
- Always return standardized envelope structure
- Never raise exceptions from public methods
- Log errors with full context before returning error envelope

### Testing
- Unit tests for isolated components (no network calls)
- Live API tests for integration with TradingView
- Use `DataValidator.reset()` in test setup/teardown

---

## Feature Matrix

| Feature | Module | Type | Timeout | Status |
|---------|--------|------|---------|--------|
| Real-time Candles | `streamer.get_candles()` | WebSocket | 15 packets | ✅ Active |
| Forecast Data | `streamer.get_forecast()` | WebSocket | 15 packets, stock-only | ✅ Active |
| Trading Ideas | `scrapers.social.ideas.get_ideas()` | HTTP | Concurrent pages | ✅ Active |
| Community Minds | `scrapers.social.minds.get_minds()` | HTTP | Cursor-based | ✅ Active |
| News Headlines | `scrapers.social.news.get_news_headlines()` | HTTP | Single request | ✅ Active |
| News Content | `scrapers.social.news.get_news_content()` | HTTP | Single request | ✅ Active |
| Screener | `scrapers.screening.screener.get_screener()` | HTTP | Concurrent pages | ✅ Active |
| Market Movers | `scrapers.market_data.market_movers.get_market_movers()` | HTTP | Single request | ✅ Active |
| Fundamentals | `scrapers.market_data.fundamentals.get_fundamentals()` | HTTP | Single request | ✅ Active |
| Pine Scripts | `scrapers.data.pine.get_script()` | HTTP | Single request | ✅ Active |

---

## Contributing

See [docs/contributing.md](docs/contributing.md) for:
- Pull request workflow
- Code review checklist
- Release process & version bumping
- Documentation updates

**Key Requirements:**
- Type hints on all public methods
- Google-style docstrings
- Unit test coverage for new features
- No breaking changes to response envelope
- Live API tests pass (TradingView connection required)
