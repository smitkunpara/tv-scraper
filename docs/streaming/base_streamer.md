# BaseStreamer API

The `BaseStreamer` class is the base class for all streaming functionality. It provides WebSocket connection management, JWT token handling, and inherits standardized response envelope methods from `BaseScraper`.

## Purpose

`BaseStreamer` is an abstract base class that should not be used directly. Instead, use the specialized streaming classes:

- `CandleStreamer` - For OHLCV and indicator data
- `ForecastStreamer` - For analyst forecast data

## Installation

```python
from tv_scraper.streaming import BaseStreamer
```

## Constructor

```python
bs = BaseStreamer(
    export_result=False,        # Save results to file
    export_type="json",        # "json" or "csv"
    cookie="<TRADINGVIEW_COOKIE>",  # Optional: session cookie
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `export_result` | `bool` | `False` | Whether to save results to file |
| `export_type` | `str` | `"json"` | Export format: `"json"` or `"csv"` |
| `cookie` | `str \| None` | `None` | TradingView session cookie |

## Methods

### `connect()`

Create and return a connected StreamHandler with JWT token.

```python
handler = bs.connect()
```

#### Returns

A connected `StreamHandler` instance.

#### Behavior

1. If `self.cookie` is provided, resolves JWT token using `get_valid_jwt_token()`
2. If no cookie, uses `"unauthorized_user_token"` for unauthenticated access
3. Creates and returns a new `StreamHandler` instance with the JWT token

#### Raises

- `Exception`: If JWT token resolution fails from an invalid cookie

#### Example

```python
from tv_scraper.streaming import CandleStreamer

cs = CandleStreamer(cookie="<TRADINGVIEW_COOKIE>")
handler = cs.connect()
# handler is now connected and ready for streaming
```

## Inheritance Hierarchy

```
BaseScraper (core/base.py)
    └── BaseStreamer (streaming/base_streamer.py)
            ├── CandleStreamer (streaming/candle_streamer.py)
            └── ForecastStreamer (streaming/forecast_streamer.py)
```

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `cookie` | `str \| None` | TradingView session cookie |
| `export_result` | `bool` | Whether to export data to file |
| `export_type` | `str` | Export format ("json" or "csv") |
| `validator` | `DataValidator` | Singleton for exchange/symbol validation |
| `study_id_to_name_map` | `dict` | Maps internal study IDs to indicator names |

## Inherited Methods

From `BaseScraper`:

### `_success_response(data, **metadata)`

Build a standardized success response.

```python
response = self._success_response(
    data={"key": "value"},
    exchange="NYSE",
    symbol="A"
)
```

### `_error_response(error, **metadata)`

Build a standardized error response.

```python
response = self._error_response(
    error="Something went wrong",
    exchange="NYSE",
    symbol="A"
)
```

### `_export(data, symbol, data_category, timeframe=None)`

Export data to file if `export_result=True`.

```python
self._export(
    data={"candles": [...]},
    symbol="BTCUSDT",
    data_category="candles",
    timeframe="1h"
)
```

## Extension Points

To create a custom streaming class, extend `BaseStreamer`:

```python
from tv_scraper.streaming import BaseStreamer
from tv_scraper.streaming.stream_handler import StreamHandler
from typing import Any

class CustomStreamer(BaseStreamer):
    """Custom streaming implementation."""

    def __init__(self, cookie: str | None = None):
        super().__init__(cookie=cookie)

    def get_custom_data(self, exchange: str, symbol: str) -> dict[str, Any]:
        handler = self.connect()

        # Your custom streaming logic
        # ...

        return self._success_response(
            data=result,
            exchange=exchange,
            symbol=symbol
        )
```

## Notes

- `BaseStreamer` is abstract - use `CandleStreamer` or `ForecastStreamer` directly
- All subclasses inherit export functionality and response envelope methods
- The `connect()` method is the primary way to get a WebSocket handler
- JWT tokens are automatically refreshed when a cookie is provided
