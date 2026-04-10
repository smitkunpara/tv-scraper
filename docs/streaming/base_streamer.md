# BaseStreamer API

`BaseStreamer` is the shared streaming base class in `tv_scraper/streaming/base_streamer.py`.
It extends `BaseScraper` and adds a single connection helper, `connect()`, plus
the `study_id_to_name_map` attribute used by indicator-aware streamers.

## Purpose

`BaseStreamer` is a concrete class, but it is primarily meant to be inherited by
higher-level streamers:

- `CandleStreamer`
- `ForecastStreamer`
- `Streamer`

## Import

```python
from tv_scraper.streaming import BaseStreamer
```

## Constructor

```python
bs = BaseStreamer(
    export_result=False,
    export_type="json",
    cookie=None,
)
```

### Constructor Arguments

| Parameter | Type | Default | Exact behavior |
|-----------|------|---------|----------------|
| `export_result` | `bool` | `False` | Stored on the instance and used by inherited `_export(...)`. |
| `export_type` | `str` | `"json"` | Validated by `BaseScraper` against `{ "json", "csv" }`. Invalid values raise `ValueError` during construction. |
| `cookie` | `str \| None` | `None` | Passed to `BaseScraper`. If `None`, `BaseScraper` falls back to `TRADINGVIEW_COOKIE` environment variable. |

### Inherited Initialization Notes

From `BaseScraper.__init__`:

- `timeout` is not exposed by `BaseStreamer`, so it remains the base default (`REQUEST_TIMEOUT`, currently `10` seconds).
- `self.cookie` becomes `cookie or os.environ.get("TRADINGVIEW_COOKIE")`.
- `self._headers` always includes `User-Agent`; it also includes `cookie` when `self.cookie` exists.

`BaseStreamer` then initializes:

```python
self.study_id_to_name_map: dict[str, str] = {}
```

## Method: connect()

```python
handler = bs.connect()
```

Creates and returns `StreamHandler(jwt_token=...)`.

### Exact Runtime Flow

1. Start with fallback token: `"unauthorized_user_token"`.
2. If `self.cookie` is truthy, lazily import `get_valid_jwt_token` and attempt JWT resolution.
3. If token resolution succeeds, use that JWT.
4. If token resolution fails, log an error and raise:
   `RuntimeError("Failed to resolve JWT token from cookie: ...")`.
5. Construct and return `StreamHandler(jwt_token=websocket_jwt_token)`.

### What "connected" means here

`StreamHandler` connects in its constructor:

- opens WebSocket connection,
- generates `quote_session` and `chart_session`,
- sends initialization messages (`set_auth_token`, `set_locale`,
  `chart_create_session`, `quote_create_session`, `quote_set_fields`,
  `quote_hibernate_all`).

So `connect()` returns a ready-initialized handler, not a lazy wrapper.

### Exceptions

- `RuntimeError` when cookie-based JWT resolution fails.
- Any exception from `StreamHandler(...)` setup is not caught in `connect()` and propagates.

## Inherited Response Envelope Expectations

`BaseStreamer` inherits response helpers from `BaseScraper`.

### Success envelope (`_success_response`)

```python
{
    "status": "success",
    "data": <payload>,
    "metadata": <merged metadata>,
    "error": None,
}
```

### Error envelope (`_error_response`)

```python
{
    "status": "failed",
    "data": <optional payload, default None>,
    "metadata": <merged metadata>,
    "error": "<error message>",
}
```

### Metadata merge behavior

Both helpers merge:

1. `self._last_metadata` (usually captured by `@catch_errors`), then
2. explicit `**metadata` passed to the helper.

Later keys overwrite earlier keys.

### `@catch_errors` expectations for subclasses

Public methods in streaming subclasses (for example `get_candles` and
`get_forecast`) are typically decorated with `@catch_errors`, which:

- captures bound, non-`None` arguments into metadata,
- converts `ValidationError` to `_error_response(str(exc), ...)`,
- converts unexpected exceptions to
  `_error_response("Unexpected error: ...", ...)`.

`connect()` itself is not decorated with `@catch_errors`, so it does not
return an envelope on failure; it raises.

## Inheritance Hierarchy

```text
BaseScraper
  └── BaseStreamer
      ├── CandleStreamer
      ├── ForecastStreamer
      └── Streamer
```

## Minimal Extension Example

```python
from typing import Any

from tv_scraper.core.base import catch_errors
from tv_scraper.streaming import BaseStreamer


class CustomStreamer(BaseStreamer):
    @catch_errors
    def get_custom_data(self, exchange: str, symbol: str) -> dict[str, Any]:
        handler = self.connect()
        # custom packet handling with handler.receive_packets()
        result = {"exchange": exchange, "symbol": symbol}
        return self._success_response(result)
```
