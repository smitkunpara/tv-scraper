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
8. [Validation & Error Architecture](#validation--error-architecture)
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
git clone https://github.com/smitkunpara/tv-scraper.git
cd tv-scraper
pip install -e .
```

### Run Tests
```bash
pytest tests/           # All tests
pytest tests/unit/      # Unit tests
pytest tests/live/      # Live TradingView API tests (live connection required)
pytest tests/integration/  # Cross-module integration tests
```

### Key Test Files
- `tests/unit/test_*.py` — Isolated component tests
- `tests/live/` — Tests requiring live TradingView connection
- `tests/integration/test_cross_module.py` — Multi-module workflows

---

## Core Technologies

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **WebSocket** | `websocket-client` (with custom framing) | Real-time streaming (candles, forecast) |
| **HTTP** | `requests` | Unified HTTP requests via `BaseScraper._request()` |
| **Object Model**| `ScannerScraper` / `BaseScraper` | Centralized network/error handling & inheritance hierarchy |
| **Error Handling**| `@catch_errors` decorator | Automated metadata capture and standardized response envelopes |
| **Validation** | Module-level functions | Symbolic/exchange verification via `tv_scraper.core.validators` |
| **Data Mapping** | Hardcoded JSON mappings | Forecast key transformation, timeframe conversion |
| **Export** | CSV/JSON writers | Optional data persistence via ``export`` arg |
| **Parallelization** | `ThreadPoolExecutor` | Concurrent page scraping (ideas) |

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

- **Most public scraper methods return envelopes** with `status/data/metadata/error`
- **`@catch_errors` methods capture exceptions** into failed envelopes
- **Status field** reflects operation outcome
- **Data field** is scraper-specific on failure (`None` or partial data)
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
- **`self._request()`**: A unified wrapper around `requests.request()` that handles timeout usage, Captcha detection, HTTP errors, and JSON parsing.
- **`self._success_response()` / `self._error_response()`**: Factory methods for generating the standardized response envelope.
- **`self._export()`**: Handles auto-saving results to JSON / CSV.

Related decorator behavior:
- **`@catch_errors`** captures bound function arguments into metadata.
- **`@catch_errors`** converts `ValidationError` and unexpected exceptions into failed envelopes.

### ScannerScraper
Extends `BaseScraper` for scanner-driven scrapers (e.g., `Fundamentals`, `Markets`, `Technicals`, `Screener`, `MarketMovers`, `SymbolMarkets`, `Calendar`, `Options`). Provides:
- **`_fetch_symbol_fields()`**: Shared `GET /symbol` helper for flat field retrieval.
- **`_map_scanner_rows()`**: Maps scanner rows (`{"s": ..., "d": [...]}`) into field-named dictionaries.

### BaseStreamer
Extends `BaseScraper` for real-time WebSocket interactions. Provides:
- **`connect()`**: Initializes the WebSocket connection on the streamer instance using either `unauthorized_user_token` or a cookie-resolved JWT.
- Runtime JWT resolution failure is raised as `RuntimeError` from `connect()`.
- Shared indicator study mapping state via `study_id_to_name_map`.

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
5. **quote_set_fields** — Subscribe to 31 quote fields (bid, ask, volume, high/low/open, etc.)
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

**Response:** Echo identical heartbeat back to server (automatically handled by `BaseStreamer.receive_packets()`)

---

## HTTP Scrapers

### Calendar Scraper

**Source:** `tv_scraper/scrapers/events/calendar.py`

**Endpoints:**
- **Dividends:** `https://scanner.tradingview.com/global/scan?label-product=calendar-dividends`
- **Earnings:** `https://scanner.tradingview.com/global/scan?label-product=calendar-earnings`

**Method Signatures:**
```python
def get_dividends(
    timestamp_from: int | None = None,
    timestamp_to: int | None = None,
    markets: list[str] | None = None,
    fields: list[str] | None = None,
    lang: str = "en",
) -> dict[str, Any]

def get_earnings(
    timestamp_from: int | None = None,
    timestamp_to: int | None = None,
    markets: list[str] | None = None,
    fields: list[str] | None = None,
    lang: str = "en",
) -> dict[str, Any]
```

**Validation & Defaults:**
- `fields` are validated only when truthy; `None` or `[]` uses defaults.
- Default window when timestamps are omitted:
  - `timestamp_from = midnight - 3 * 86400`
  - `timestamp_to = midnight + 3 * 86400 + 86399`
- `markets` and `lang` are passed through without local validation.

**Data Extraction:**
```
1. Build scanner payload with columns + in_range filter on event date columns.
2. POST to calendar scanner endpoint.
3. Read json_response["data"]; if not list, fallback to [].
4. Map scanner rows via _map_scanner_rows(items, selected_fields).
```

**Output Fields (per row):**
```python
{
    "symbol": str,
    "<requested_field>": Any,
    ...
}
```

**Known Behavior Nuances:**
- Returns success with empty list when no events are found.
- Adds metadata: `event_type`, `total`, `timestamp_from`, `timestamp_to`, and optional `markets`.
- These methods are not decorated with `@catch_errors`; handled failures are normalized, but unexpected runtime exceptions are not auto-wrapped.

### Fundamentals Scraper

**Source:** `tv_scraper/scrapers/market_data/fundamentals.py`

**Endpoint:** `https://scanner.tradingview.com/symbol`

**Method Signature:**
```python
def get_fundamentals(
    exchange: str,
    symbol: str,
    fields: list[str] | None = None,
) -> dict[str, Any]
```

**Validation:**
- `fields` must be `list[str]` or `None`.
- `fields=None` or `fields=[]` fetches all `ALL_FIELDS`.
- `validate_fields(field_list, ALL_FIELDS, "field")`.
- Live symbol validation happens inside `_fetch_symbol_fields()`.

**Data Extraction:**
```
1. Verify exchange:symbol via verify_symbol_exchange().
2. GET /symbol with fields=<comma-separated requested fields> and no_404=true.
3. Build output dict: {"symbol": "EXCHANGE:SYMBOL", field: response.get(field), ...}.
4. Missing fields are kept with value None.
```

**Output Structure:**
```python
{
    "symbol": str,
    "<fundamental_field>": Any | None,
    ...
}
```

**Known Behavior Nuances:**
- `DEFAULT_COMPARISON_FIELDS` exists but is not used by `get_fundamentals()`.
- Empty/falsy parsed payload returns failed response: `"No data returned from API."`.

### Markets Scraper

**Source:** `tv_scraper/scrapers/market_data/markets.py`

**Endpoint:** `https://scanner.tradingview.com/{market}/scan`

**Method Signature:**
```python
def get_markets(
    market: str = "america",
    sort_by: str = "market_cap",
    fields: list[str] | None = None,
    sort_order: str = "desc",
    limit: int = 50,
) -> dict[str, Any]
```

**Validation:**
- `market` in `VALID_MARKETS`.
- `sort_by` in `SORT_CRITERIA`.
- `sort_order` in `{"asc", "desc"}`.
- `limit` in `[1, 1000]`.
- `fields` are not validated by this method.

**Data Extraction:**
```
1. Build payload with columns, sort, range, options.lang="en", and STOCK_FILTERS.
2. POST scanner request.
3. If data is empty, return failed response.
4. Map scanner rows via _map_scanner_rows().
```

**Output Fields (per row):**
```python
{
    "symbol": str,
    "<requested_field>": Any | None,
    ...
}
```

**Known Behavior Nuances:**
- Built-in filters force stock + non-empty market cap.
- Although non-stock markets are accepted by validation (`crypto`, `forex`), stock-only filters may produce empty results and a failed envelope.

### Options Scraper

**Source:** `tv_scraper/scrapers/market_data/options.py`

**Data Endpoint:** `https://scanner.tradingview.com/options/scan2?label-product=symbols-options`

**Method Signatures:**
```python
def get_options(
    exchange: str,
    symbol: str,
    expiration: int | None = None,
    strike: int | float | None = None,
        columns: list[OPTION_COLUMN_LITERAL] | None = None,
) -> dict[str, Any]
```

**Validation:**
- The method calls `verify_options_symbol(exchange, symbol)`.
- `columns` are validated against `DEFAULT_OPTION_COLUMNS` when provided.
- At least one filter must be provided: `expiration`, `strike`, or both.
- `expiration` is validated by `validate_yyyymmdd_date("expiration", expiration)` when provided.
    - Format must be 8-digit `YYYYMMDD`.
    - Month range: `0 < MM <= 12`.
    - Day range: `0 < DD <= 31`.
    - Calendar validity is enforced (for example, 31 February is rejected).
- `strike` must be `int | float` when provided.

**Data Extraction:**
```
1. Build payload with base option filter + index_filters on underlying_symbol.
2. Add expiration and/or strike filters depending on provided arguments.
2. POST options scanner endpoint.
3. Parse response fields list + symbols list.
4. Map each symbol row: {"symbol": item["s"], field_i: values[i], ...}.
```

**Output Fields (per option row):**
```python
{
    "symbol": str,
    "ask": float | None,
    "bid": float | None,
    "strike": float | int | None,
    ...
}
```

**Known Behavior Nuances:**
- Error messages with `"404"` are rewritten to "options chain not found" wording.
- Empty `symbols` list returns failed response.
- Success metadata includes `total` and `filter_value`.
- Combined filtering (`expiration` + `strike`) returns metadata `filter_value` as a dict.

### Technicals Scraper

**Source:** `tv_scraper/scrapers/market_data/technicals.py`

**Endpoint:** `https://scanner.tradingview.com/symbol`

**Method Signature:**
```python
def get_technicals(
 exchange: str,
 symbol: str,
 timeframe: str = "1d",
 technical_indicators: list[str] | None = None,
) -> dict[str, Any]
```

**Validation Flow:**
```
1. validate_exchange(exchange)
2. validate_symbol(exchange, symbol)
3. validate_timeframe(timeframe)
4. resolve indicators:
 - technical_indicators=None -> fetch all INDICATORS
 - technical_indicators provided -> validate_indicators(technical_indicators)
5. verify_symbol_exchange(exchange, symbol) # live check
```

**Data Extraction:**
```
1. Build fields param from requested indicators.
 - Daily (1D): indicator keys are unsuffixed.
 - Non-daily: indicator keys are suffixed (e.g. RSI|60).
2. GET /symbol with no_404=true.
3. Build result dict from response.get(indicator_key).
4. Strip timeframe suffix from output keys for non-daily timeframes.
```

**Output Fields:**
```python
{
 "RSI": float | None,
 "MACD.macd": float | None,
 ...
}
```

**Known Behavior Nuances:**
- Missing indicator keys are returned as `None` (not an automatic failure).
- Method signature simplified in v1.4.0b2: removed `all_indicators` and `fields` parameters.

### Screener Scraper

**Source:** `tv_scraper/scrapers/screening/screener.py`

**Endpoint:** `https://scanner.tradingview.com/{market}/scan`

**Method Signature:**
```python
def get_screener(
    market: str = "america",
    filters: list[dict[str, Any]] | None = None,
    fields: list[str] | None = None,
    sort_by: str | None = None,
    sort_order: str = "desc",
    limit: int = 50,
    symbols: dict[str, Any] | None = None,
    filter2: dict[str, Any] | None = None,
) -> dict[str, Any]
```

**Validation:**
- `market` choice validation.
- `sort_order` in `{"asc", "desc"}`.
- `limit` in `[1, 10000]`.
- `filters` entries must be dicts with `left` and valid `operation`.
- `filter2` must be dict with `operator` key.
- `fields`, `sort_by`, and `symbols` are not schema-validated here.

**Data Extraction:**
```
1. Build payload with columns, options.lang="en", range, and markets=[market].
2. Add filter/sort/symbols/filter2 only when inputs are truthy.
3. POST scanner endpoint.
4. Map rows via _map_scanner_rows().
5. Return total + total_available metadata.
```

**Known Behavior Nuances:**
- Empty result sets return success with `data=[]`.
- `filters=[]`, `symbols={}`, and `filter2={}` are omitted from payload due truthy checks.

### Market Movers Scraper

**Source:** `tv_scraper/scrapers/screening/market_movers.py`

**Endpoint Mapping:**
- `stocks-usa -> /america/scan`
- `stocks-uk -> /uk/scan`
- `stocks-india -> /india/scan`
- `stocks-australia -> /australia/scan`
- `stocks-canada -> /canada/scan`
- `crypto -> /crypto/scan`
- `forex -> /forex/scan`
- `bonds -> /bonds/scan`
- `futures -> /futures/scan`

**Method Signature:**
```python
def get_market_movers(
    market: str = "stocks-usa",
    category: str = "gainers",
    fields: list[str] | None = None,
    limit: int = 50,
    language: str = "en",
) -> dict[str, Any]
```

**Validation:**
- `limit` in `[1, 1000]`.
- `market` in supported list.
- `category` allowed set depends on stock vs non-stock market.
- `language` validated via `validate_language()`.
- Field validation checks list-of-strings shape, but not against a fixed global allowlist.

**Data Extraction:**
```
1. Resolve market-specific default fields.
2. Build category sort config and filter conditions.
3. POST scanner endpoint.
4. Map scanner rows and return total + totalCount metadata.
```

**Category Filter Nuances:**
- Stock markets add `market == <scanner_segment>` filter.
- `penny-stocks` adds `close < 5`.
- Gainers/losers variants add `change > 0` / `change < 0`.
- No explicit `type=stock` filter is added.

### Symbol Markets Scraper

**Source:** `tv_scraper/scrapers/screening/symbol_markets.py`

**Endpoint:** `https://scanner.tradingview.com/{scanner}/scan`

**Method Signature:**
```python
def get_symbol_markets(
    exchange: str,
    symbol: str,
    fields: list[str] | None = None,
    scanner: str = "global",
    limit: int = 150,
) -> dict[str, Any]
```

**Validation:**
- `validate_exchange(exchange)`.
- `validate_symbol(exchange, symbol)`.
- `scanner` choice validation.
- `limit` in `[1, 1000]`.
- `fields` are not field-name validated here.

**Data Extraction:**
```
1. Build payload with filter: {left:"name", operation:"match", right:search_symbol}.
2. POST scanner endpoint.
3. Map rows via _map_scanner_rows().
4. Return failed response if mapped result is empty.
```

**Known Behavior Nuances:**
- Failure message on empty data uses original input symbol, not parsed `search_symbol`.
- Success metadata includes `total` and `total_available`.

### Pine Scraper

**Source:** `tv_scraper/scrapers/scripts/pine.py`

**Facade Base URL:** `https://pine-facade.tradingview.com/pine-facade`

**Public Methods:**
```python
list_saved_scripts() -> dict[str, Any]
validate_script(source: str) -> dict[str, Any]
get_script(pine_id: str, version: str) -> dict[str, Any]
create_script(name: str, source: str) -> dict[str, Any]
edit_script(pine_id: str, name: str, source: str) -> dict[str, Any]
delete_script(pine_id: str) -> dict[str, Any]
```

**Authentication & Validation:**
- All methods require cookie authentication (`_validate_cookie_required()`).
- Empty input validation is handled for `source`, `pine_id`, `version`, and `name` where applicable.
- `create_script()` and `edit_script()` run `validate_script()` before save calls.

**Endpoint Coverage:**
- `GET /list?filter=saved`
- `POST /translate_light?v=3` (multipart source)
- `GET /get/{encoded_pine_id}/{encoded_version}`
- `POST /save/new` (params: `name`, `allow_overwrite=true`)
- `POST /save/next/{encoded_pine_id}` (params: `allow_create_new=false`, `name`)
- `POST /delete/{encoded_pine_id}`

**Output Nuances:**
- `validate_script()` returns failed response when compiler `errors` exists; warnings are preserved in metadata.
- `create_script()` / `edit_script()` return `{"id", "name", "warnings"}` on success.
- `delete_script()` succeeds only when parsed response equals string `"ok"`.
- Export support is used by `list_saved_scripts()` and `get_script()`; create/edit/delete do not export.

### Ideas Scraper

**Source:** `tv_scraper/scrapers/social/ideas.py`
Extends `BaseScraper`.

**Endpoints:**
- **Page 1:** `https://www.tradingview.com/symbols/{EXCHANGE}-{SYMBOL}/ideas/`
- **Page N (N>1):** `https://www.tradingview.com/symbols/{EXCHANGE}-{SYMBOL}/ideas/page-{N}/`

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
1. Validate: start_page >= 1 and end_page >= start_page
2. Validate symbol/exchange via verify_symbol_exchange() and sort_by via validate_choice()
3. Build page range [start_page, end_page] and scrape concurrently via ThreadPoolExecutor(max_workers=self._max_workers)
4. For each page: GET endpoint with `component-data-only=1` (+ `sort=recent` when needed)
5. Parse JSON defensively: data -> ideas -> data -> items (fallback to empty containers on type mismatch)
6. Map each item via _map_idea() static method
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
- Validation: `start_page`/`end_page` checks plus module-level validators
- Partial page failures: returns `status="failed"` with `failed_pages`, `total` collected, and `pages` metadata
- Non-dict page payloads are logged and treated as empty page results
- `as_completed(..., timeout=self.timeout*2)` timeout is caught by decorator and returned as an `Unexpected error` failed envelope

**Known Behavior Nuances:**
- Result ordering follows future completion order, not guaranteed page order.
- If any page fails, collected articles are counted in metadata but not returned in `data` (failed envelope).

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
3. Parse each item via _parse_mind() (author normalization + created timestamp formatting)
4. Extract cursor from "next" URL query (`?c=`) for pagination
5. Continue until no next cursor, empty results, or MAX_PAGES (100) reached
6. Client-side limit trimming: parsed_data[:limit] (applied after fetch loop)
7. Capture symbol_info from response.meta.symbols_info[{EXCHANGE}:{SYMBOL}] when present
```

**Output Fields (per mind):**
```python
{
    "text": str,                          # Idea text
    "url": str,                           # Link to idea
    "author": {
        "username": str,
        "profile_url": str,               # Relative URL normalized to absolute tradingview.com URL
        "is_broker": bool                 # Broker flag
    },
    "created": str,                       # "YYYY-MM-DD HH:MM:SS" if ISO-8601 parseable, else raw value
    "total_likes": int,
    "total_comments": int
}
```

**Validation & Pagination:**
- Symbol/exchange verified via `verify_symbol_exchange()`
- Cursor-based pagination (`next` URL) with `MAX_PAGES=100` guard
- No explicit validation for `limit` in current implementation

**Known Behavior Nuances:**
- `limit` truncation runs after pagination completes.
- Request failure at any page returns failed response and does not include partially collected rows in `data`.

### News Scraper

**Source:** `tv_scraper/scrapers/social/news.py`

**Endpoints:**
- **News Flow (v2):** `https://news-mediator.tradingview.com/news-flow/v2/news`
- **Headlines (Legacy):** `https://news-headlines.tradingview.com/v2/view/headlines/symbol`
- **Story Content:** `https://news-mediator.tradingview.com/public/news/v1/story`

**Method Signatures:**
```python
def get_news(
    exchange: str | None = None,
    symbol: str | None = None,
    corp_activity: list[str] | None = None,
    economic_category: list[str] | None = None,
    market: list[str] | None = None,
    market_country: list[str] | None = None,
    provider: list[str] | None = None,
    sector: list[str] | None = None,
    language: str = "en",
    limit: int = 50
) -> dict[str, Any]

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

**News Flow (v2) Query Construction:**
- Uses multiple `filter` parameters: `?filter=lang:en&filter=symbol:OANDA:XAUUSD&...`
- Filters are comma-separated within the key: `filter=market_country:US,IN,GB`
- **URL Length Guard:** Pre-flight check throws `ValidationError` if the total URL exceeds **4096 characters** (safety limit for TradingView servers).

**Headline Extraction (v2):**
```
1. Validate inputs against strict Literals (Providers, Countries, Sectors, etc.).
2. Build dynamic filter list and encode as multiple "filter" params.
3. Perform URL length verification.
4. HTTP GET to Mediator flow endpoint.
5. Parse JSON and truncate to client-side limit.
6. Map rich fields: urgency, permission, relatedSymbols, provider object, is_flash.
```

**Story Parsing (Complex):**
```
1. HTTP GET to story endpoint with story_id.
2. Parse ast_description.children.
3. Keep only top-level paragraph nodes (type="p").
4. For each paragraph, merge plain string nodes and dict node params.text values.
5. Join paragraph texts with \n separator.
```

**News Flow Output Fields:**
```python
{
    "id": str,
    "title": str,
    "published": int,
    "urgency": int,
    "permission": str,
    "relatedSymbols": list[dict],
    "storyPath": str,
    "provider": {
        "id": str,
        "name": str,
        "logo_id": str
    },
    "is_flash": bool
}
```

**Legacy Headline Output Fields:**
```python
{
    "id": str,
    "title": str,
    "shortDescription": str,
    "published": int,
    "storyPath": str
}
```

**Story Output Fields:**
```python
{
    "id": str,
    "title": str,
    "description": str,                 # Merged AST paragraphs
    "published": int,
    "storyPath": str
}
```

**Validation:**
- `get_news`: strict Literal validation for Country/Provider/Sector/Activity/Market/Category
- `get_news_headlines`: verify symbol/exchange + validate language/provider/area/sort_by/section
- `get_news_content`: `story_id` must be non-empty + validate language
- **URL Limit:** Pre-flight check enforces **4096 character** maximum for `get_news()` filter strings.
- sort_by: Must be in `{"latest", "oldest", "most_urgent", "least_urgent"}`
- section: Must be in `{"all", "esg", "press_release", "financial_statement"}`
- language: Validated against `validation_data.LANGUAGES` values (e.g., `"en"`, `"fr"`)
- provider: Validated against `validation_data.NEWS_PROVIDERS` (expanded in News v2)
- country: Validated against `validation_data.NEWS_COUNTRIES`
- sector: Validated against `validation_data.NEWS_SECTORS`
- area: Validated against `validation_data.AREAS` (keys or mapped codes)

**Known Behavior Nuance:**
- `area` values passed as area codes (e.g. `"WLD"`) validate, but `AREAS.get(area, "")` sends empty area filter for those code inputs.
- Mediator API `get_news()` applies the `limit` client-side after initial fetch.

---

## Streaming Methods

### BaseStreamer.connect()

**Source:** `tv_scraper/streaming/base_streamer.py`

**Method Signature:**
```python
def connect(self) -> None:
```

**Flow:**
```
1. Start with websocket_jwt_token="unauthorized_user_token".
2. If cookie exists, resolve JWT via get_valid_jwt_token(cookie).
3. On JWT resolution failure, raise RuntimeError.
4. Create the WebSocket connection, initialize quote/chart sessions, and store state on the instance.
```

**Known Behavior Nuance:**
- `connect()` is not wrapped by `@catch_errors`; it raises on failure.

### CandleStreamer.get_candles()

**Source:** `tv_scraper/streaming/candle_streamer.py`

**Method Signature:**
```python
def get_candles(
 self,
 exchange: str,
 symbol: str,
 timeframe: str = "1m",
 numb_candles: int = 10,
 indicators: list[tuple[str, str]] | None = None,
) -> dict[str, Any]
```

**Validation:**
- `verify_symbol_exchange(exchange, symbol)`
- `validate_timeframe(timeframe)`
- `validate_range("numb_candles", numb_candles, 1, 5000)`

**WebSocket Flow:**
```
1. Connect and initialize quote/chart sessions.
2. Add symbol to both sessions via quote_add_symbols, resolve_symbol, create_series, quote_fast_symbols.
3. If indicators requested:
 - For standard indicators: fetch study metadata and send create_study per indicator.
 - For custom Pine scripts: validate script via Pine validator before creating studies.
4. Consume packets:
 - timescale_update -> OHLCV extraction
 - du -> indicator extraction
5. Break when OHLCV and indicators are ready, or when packet index i > 15.
```

**Stop Conditions:**
```
1. len(ohlcv_data) >= numb_candles AND indicator readiness satisfied, OR
2. packet index timeout: i > 15
```

**Data Extraction Logic:**
```python
# OHLCV from p[1].sds_1.s
{
 "index": entry["i"],
 "timestamp": entry["v"][0],
 "open": entry["v"][1],
 "high": entry["v"][2],
 "low": entry["v"][3],
 "close": entry["v"][4],
 # "volume" included only when len(entry["v"]) > 5
}

# Indicator rows from du packet studies
{
 "index": item["i"],
 "timestamp": item["v"][0],
 "0": item["v"][1],
 "1": item["v"][2],
 ...
}
```

**Output Structure (Success):**
```python
{
 "status": "success",
 "data": {
 "ohlcv": [ ... ],
 "indicators": {
 "STD;RSI": [ ... ]
 }
 },
 "metadata": {
 "exchange": str,
 "symbol": str,
 "timeframe": str,
 "numb_candles": int,
 # indicators included when provided
 },
 "error": None
}
```

**Failure Nuances:**
- Returns failed if no OHLCV data is received.
- Returns failed if one or more requested indicator IDs are missing after capture.
- Custom Pine indicator validation failures return clear error messages instead of continuing silently.
- Indicator metadata or study creation failures are raised internally and wrapped by `@catch_errors` as `Unexpected error` failed envelopes.

**Additional CandleStreamer Methods (v1.4.0b2+):**

- `stream_realtime_price(exchange, symbol) -> Generator`: Persistent generator yielding real-time price updates from WebSocket streams.
- `get_available_indicators() -> dict`: Static method returning available built-in TradingView indicators.

### ForecastStreamer.get_forecast()

**Source:** `tv_scraper/streaming/forecast_streamer.py`

**Method Signature:**
```python
def get_forecast(self, exchange: str, symbol: str) -> dict[str, Any]
```

**Validation Flow:**
```
1. verify_symbol_exchange(exchange, symbol)
2. Resolve symbol type via direct requests.get to /symbol with fields=type.
3. If type != "stock", raise ValidationError.
```

**WebSocket Subscription:**
```
1. Connect quote session.
2. set_data_quality("low")
3. quote_set_fields(qs, *capture_fields)
4. quote_hibernate_all(qs)
5. quote_add_symbols(qs, resolved symbol)
6. quote_fast_symbols(qs, exchange_symbol)
7. Capture qsd packets and merge snapshot values.
```

**Output Key Mapping (fixed 10 keys):**
```python
{
    "revenue_currency": "fundamental_currency_code",
    "previous_close_price": "regular_close",
    "average_price_target": "price_target_average",
    "highest_price_target": "price_target_high",
    "lowest_price_target": "price_target_low",
    "median_price_target": "price_target_median",
    "yearly_eps_data": "earnings_fy_h",
    "quarterly_eps_data": "earnings_fq_h",
    "yearly_revenue_data": "revenues_fy_h",
    "quarterly_revenue_data": "revenues_fq_h",
}
```

**Stop Conditions:**
```
1. All required output keys found with non-None values, OR
2. packet_count > 15 (timeout warning logged)
```

**Output Behavior:**
- Success: all 10 mapped keys available, metadata includes `available_output_keys`.
- Partial/timeout: failed response with `data` containing all 10 keys (missing values as `None`) and `available_output_keys` metadata.
- Non-stock symbol: failed response via validation error.

**Known Behavior Nuance:**
- `packet_count > 15` timeout check is executed inside the `qsd` parse branch.

### Streamer Facade

**Source:** `tv_scraper/streaming/streamer.py`

**Facade Methods:**
```python
def get_candles(...) -> dict[str, Any]
def get_forecast(...) -> dict[str, Any]
def stream_realtime_price(...) -> Generator[dict[str, Any], None, None]
@staticmethod
def get_available_indicators() -> dict[str, Any]
```

**Delegation Model:**
- `get_candles()` delegates to `CandleStreamer.get_candles()`.
- `get_forecast()` delegates to `ForecastStreamer.get_forecast()`.
- `get_available_indicators()` returns `fetch_available_indicators()` directly.

**Export Nuance:**
- When data is exported, delegated streamers handle the file writing on success.
- This can result in duplicate export writes for successful `get_candles()` / `get_forecast()` calls.

**Realtime Price Generator (`stream_realtime_price`)**

**Validation & Setup:**
```
1. verify_symbol_exchange(exchange, symbol)
2. connect()
3. subscribe quote session (quote_add_symbols, quote_fast_symbols)
4. subscribe chart session with 1m series (resolve_symbol, create_series(..., "1", 1, ""))
```

**Yielded Packet Mapping:**
- `qsd` packets yield quote-centric dictionaries (price, volume, bid/ask, OHLC day values, etc.).
- `du` packets yield close-based updates from the 1m chart series.

**Known Behavior Nuances:**
- Generator runs until stream ends; no internal max packet stop condition.
- This method is not envelope-wrapped and may raise during iteration (validation/connect/network/runtime errors).

### BaseStreamer WebSocket Implementation

**Source:** `tv_scraper/streaming/base_streamer.py`

**Core Methods:**

| Method | Purpose | Returns |
|--------|---------|---------|
| `_generate_session(prefix="qs_")` | Create unique session ID | `"qs_abcdefghijklm"` |
| `_send_msg(method, params)` | Build and send JSON-RPC message | None |
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
- The connected socket is stored on the streamer instance

---

## Validation & Error Architecture

### @catch_errors Decorator
The primary mechanism for standardizing responses. Most public scraper methods are decorated with `@catch_errors`, which:
1. **Captures Metadata**: Uses `inspect.signature` to automatically bind all function arguments (e.g., `symbol`, `exchange`, `limit`) into the response's `metadata` field.
2. **Standardizes Envelopes**: Wraps the function's return value in a `success` envelope or catches `ValidationError` / network exceptions to return a `failed` envelope.
3. **Eliminates Boilerplate**: Removes the need for manual `try/except` blocks and manual metadata dictionary construction in every method.

Notable exceptions in this codebase include methods such as `Calendar.get_dividends/get_earnings`, `BaseStreamer.connect()`, and `Streamer.stream_realtime_price()`.

### Validation Architecture
Validation logic is decentralized and integrated directly into the scraper classes. High-frequency validation utilities are provided by `BaseScraper`, while specialized validation is encapsulated within individual scrapers.

| Method | Source | Purpose |
|--------|--------|---------|
| `self._verify_symbol_exchange(exc, sym)` | `BaseScraper` | Live check against TradingView for symbol existence. |
| `self._validate_choice(name, val, choices)`| `BaseScraper` | Generic validator for string literal choices. |
| `self._validate_list(name, vals, choices)` | `BaseScraper` | Batch counterpart to `_validate_choice`. |
| `self._validate_range(name, val, min, max)` | `BaseScraper` | Generic numeric range validator. |
| `self._validate_timeframe(tf)` | `BaseScraper` | Validates TradingView-compatible timeframe strings. |
| `self._validate_indicators(indicators)` | `Technicals` | Validates a list of requested technical indicators. |
| `self._verify_options_symbol(exc, sym)` | `Options` | Specifically verifies if a symbol has an options market. |
| `self._validate_yyyymmdd_date(name, val)` | `Options` | Validates integer dates in `YYYYMMDD` format. |

**Design Rule:** Public methods should perform validation at the very beginning by calling these internal methods. Any `ValidationError` raised will be automatically caught by `@catch_errors` and formatted into a standardized error response.

---

### Validation Methods

#### Exchange Validation: `_validate_choice(exchange.upper(), EXCHANGES_SET)`

**Type:** Offline check

**Logic:**
1. Case-insensitive match: `exchange.upper() in _EXCHANGES_SET`
2. On failure: Use `difflib.get_close_matches(cutoff=0.6, n=5)` for suggestions
3. Return sample of valid exchanges in error message

**Example:**
```python
# Internal call
self._validate_choice(exchange_up, _EXCHANGES_SET)
# On failure, raises ValidationError: "Invalid value: 'NASDQ'. Did you mean: 'NASDAQ'? Allowed values include: NYSE, NASDAQ, ..."
```

#### Symbol Validation

**Type:** Offline check (Integrated in `_verify_symbol_exchange`)

**Logic:**
1. `isinstance(symbol, str)`
2. `symbol.strip()` is not empty
3. No special character validation internally, relying on HTTP check for validity.

#### Symbol-Exchange Verification: `_verify_symbol_exchange(exchange: str, symbol: str) -> tuple[str, str]`

**Type:** Two-stage (offline + online)

**Stage 1 - Offline:**
1. Verify `exchange` and `symbol` are provided and are non-empty strings.
2. Call `_validate_choice(exchange_up, _EXCHANGES_SET)`

**Stage 2 - Online (HTTP):**
- HTTP GET to TradingView scanner API: `https://scanner.tradingview.com/symbol?symbol={EXCHANGE}%3A{SYMBOL}&fields=market&no_404=false`
- On 404: Raise `ValidationError("Symbol '{symbol}' not found on exchange '{exchange}'")`
- On network error: Fails silently or raises depending on context (usually wrapped by `@catch_errors`).
- On other HTTP error: Raise `ValidationError` with status code in message

#### Indicator Validation: `_validate_indicators(indicators: list[str])`

**Type:** Offline check (Class-specific to `Technicals`)

**Logic:**
1. List is non-empty
2. Each indicator in `_INDICATORS_SET`
3. Use `difflib` suggestions on first invalid indicator

### Validation Datasets

Validator allowlists are sourced from `tv_scraper.core.validation_data` constants:

```python
EXCHANGES, INDICATORS, TIMEFRAMES, NEWS_PROVIDERS, LANGUAGES, AREAS
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
- Prefer envelope-based failures in public scraper methods; some streaming/connection helpers intentionally raise
- Log errors with full context before returning error envelope

### Testing
- Unit tests for isolated components (no network calls)
- Live API tests for integration with TradingView
- Keep validator/network state isolated across tests (mock external calls in unit tests)
- **Edge Case Verification:** For each new feature or scraper method, comprehensive test cases MUST be created to verify edge cases and failure modes.

---

## Feature Matrix

| Feature | Module | Type | Timeout | Status |
|---------|--------|------|---------|--------|
| Calendar Events | `scrapers.events.calendar.get_dividends/get_earnings` | HTTP (Scanner) | Single request (default +/-3 day range) | ✅ Active |
| Fundamentals | `scrapers.market_data.fundamentals.get_fundamentals()` | HTTP (Scanner /symbol) | Single request | ✅ Active |
| Markets Ranking | `scrapers.market_data.markets.get_markets()` | HTTP (Scanner) | Single request | ✅ Active |
| Options Chain | `scrapers.market_data.options.get_options()` | HTTP (Options Scanner) | Single request | ✅ Active |
| Technical Indicators | `scrapers.market_data.technicals.get_technicals()` | HTTP (Scanner /symbol) | Single request | ✅ Active |
| Screener | `scrapers.screening.screener.get_screener()` | HTTP (Scanner) | Single request | ✅ Active |
| Market Movers | `scrapers.screening.market_movers.get_market_movers()` | HTTP (Scanner) | Single request | ✅ Active |
| Symbol Markets | `scrapers.screening.symbol_markets.get_symbol_markets()` | HTTP (Scanner) | Single request | ✅ Active |
| Pine Scripts | `scrapers.scripts.pine.*` | HTTP (Pine Facade) | Single request per operation | ✅ Active |
| Trading Ideas | `scrapers.social.ideas.get_ideas()` | HTTP | Concurrent pages | ✅ Active |
| Community Minds | `scrapers.social.minds.get_minds()` | HTTP | Cursor-based | ✅ Active |
| News Flow (v2) | `scrapers.social.news.get_news()` | HTTP (Mediator) | Multi-filter safety check | ✅ Active |
| News Headlines (Legacy) | `scrapers.social.news.get_news_headlines()` | HTTP | Single request | ✅ Active |
| News Content | `scrapers.social.news.get_news_content()` | HTTP | Single request | ✅ Active |
| Candle Streaming | `streaming.candle_streamer.CandleStreamer.get_candles()` | WebSocket | Packet loop with `i > 15` timeout break | ✅ Active |
| Forecast Streaming | `streaming.forecast_streamer.ForecastStreamer.get_forecast()` | WebSocket + HTTP type check | Packet loop with `packet_count > 15` timeout break | ✅ Active |
| Realtime Price Stream | `streaming.streamer.Streamer.stream_realtime_price()` | WebSocket Generator | Continuous until stream closes | ✅ Active |

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
- Unit test coverage for new features, including edge case verification
- No breaking changes to response envelope
- Live API tests pass (TradingView connection required)
