# Getting Started

This page is the shortest path to a successful request. It covers install, the common call pattern, exports, cookies, and one invalid-input example so you can see how failures look.

## Install

```bash
pip install tv-scraper
```

Or with `uv`:

```bash
uv add tv-scraper
```

For local development:

```bash
git clone https://github.com/smitkunpara/tv-scraper.git
cd tv-scraper
uv sync --extra dev
```

## First Successful Call

```python
from tv_scraper import Technicals

scraper = Technicals()
result = scraper.get_technicals(
    exchange="NASDAQ",
    symbol="AAPL",
    technical_indicators=["RSI", "MACD.macd"],
)

if result["status"] == "success":
    print(result["data"])
else:
    print(result["error"])
```

Output structure (success):

```python
{
    "status": "success",
    "data": {"RSI": 54.21, "MACD.macd": 0.15},
    "metadata": {
        "exchange": "NASDAQ",
        "symbol": "AAPL",
        "timeframe": "1d",
        "technical_indicators": ["RSI", "MACD.macd"],
    },
    "error": None,
}
```

Output structure (failure):

```python
{
    "status": "failed",
    "data": None,
    "metadata": {"exchange": "INVALID", "symbol": "AAPL", "technical_indicators": ["RSI"]},
    "error": "Invalid value: 'INVALID'. ...",
}
```

Use this same pattern across the library:

1. Create the scraper or streamer.
2. Call a public method with keyword arguments.
3. Check `result["status"]`.
4. Read `result["data"]` on success or `result["error"]` on failure.

## Common Input Pattern

Most symbol-based methods take `exchange` and `symbol` separately:

```python
result = scraper.get_technicals(exchange="NASDAQ", symbol="AAPL")
```

To find accepted values quickly, jump straight to:

- [Exchanges](supported_data.md#exchanges)
- [Technical indicators](supported_data.md#technical-indicators)
- [Timeframes](supported_data.md#timeframes)
- [Languages](supported_data.md#languages)

## Response Shape

All public methods return the same outer envelope:

```python
{
    "status": "success" | "failed",
    "data": ...,
    "metadata": {...},
    "error": None | "message",
}
```

## Exports

Most scrapers can export successful responses to JSON or CSV:

```python
from tv_scraper import Technicals

scraper = Technicals(export="json")
result = scraper.get_technicals(
    exchange="NASDAQ",
    symbol="AAPL",
    technical_indicators=["RSI"],
)
```

Supported export formats:

- `"json"`
- `"csv"`

Invalid export formats are one of the few cases that fail at construction time:

```python
Technicals(export="xml")
```

## Cookie-Based Features

A cookie is optional for most HTTP scrapers, but required for:

- [Pine](scrapers/pine.md)
- authenticated streaming flows such as custom indicator access

The library will use `TRADINGVIEW_COOKIE` automatically when the constructor `cookie` argument is omitted. See [Getting Cookies](getting_cookies.md).

!!! failure "wrong input"
    This input shape is wrong because `exchange` and `symbol` are separate arguments.

    ```python
    scraper.get_technicals(exchange="NASDAQ:AAPL", symbol="AAPL")
    ```

    Use this instead:

    ```python
    scraper.get_technicals(exchange="NASDAQ", symbol="AAPL")
    ```

## Next Steps

- Want exact request rules and response behavior: [API Basics](api-conventions.md)
- Need a method-specific page: browse the [scraper docs](index.md#choose-by-task)
- Need valid values fast: [Validation & Supported Values](supported_data.md)
