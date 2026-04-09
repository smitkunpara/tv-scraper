# Pine Scraper

## Overview

The Pine scraper provides authenticated TradingView Pine script management APIs.

## ✨ Highlight: Pine -> Streamer Custom Indicator Workflow

The primary purpose of Pine support is to power custom indicator workflows in Streamer:

- Create and maintain your own Pine indicator scripts from Python.
- Merge multiple indicator calculations into one Pine script.
- Fetch the merged output through Streamer as a single custom indicator feed.

This lets you centralize strategy logic in one Pine script while consuming the values in your market-data pipeline.

Why teams use this pattern:

- Some TradingView plans cap concurrent indicator usage (for example, 2 indicators on free usage).
- A merged custom Pine script can expose multiple signals while occupying one custom indicator stream target.

Current support includes:

- View your saved Pine scripts
- Fetch full script source by id and version
- Validate Pine source code
- Create new scripts
- Edit existing scripts
- Delete scripts

Cookie authentication is required for all Pine operations.

## Common Workflow (Merged Indicators)

Use Pine methods to maintain a script that combines multiple indicator calculations (for example, RSI + EMA + ATR in one script), then fetch that custom indicator through Streamer.

```python
from tv_scraper.scrapers.scripts import Pine
from tv_scraper.streaming import Streamer

pine = Pine(cookie="<TRADINGVIEW_COOKIE>")
streamer = Streamer()

source_code = """
//@version=6
indicator("My Multi Indicator", overlay=false)

rsi = ta.rsi(close, 14)
ema = ta.ema(close, 21)
atr = ta.atr(14)

plot(rsi, title="RSI")
plot(ema, title="EMA")
plot(atr, title="ATR")
"""

# Create or update your script in TradingView
pine.create_script(name="My Multi Indicator", source=source_code)

# Then fetch your saved script id/version pair
saved = pine.list_saved_scripts()
first_script = saved["data"][0]

# Use the corresponding custom indicator id/version in Streamer
result = streamer.get_candles(
    exchange="BINANCE",
    symbol="BTCUSDT",
    timeframe="1h",
    numb_candles=100,
    indicators=[(first_script["id"], str(first_script["version"]))],
)
```

> Note: For custom scripts, use `pine.list_saved_scripts()` and pass that exact `id` + `version` pair into `indicators` when calling `Streamer.get_candles()`.

## Import and Constructor

```python
import os
from tv_scraper.scrapers.scripts import Pine

pine = Pine(
    export_result=False,
    export_type="json",
    timeout=10,
    cookie=os.environ.get("TRADINGVIEW_COOKIE"),
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `export_result` | `bool` | `False` | Export output to file |
| `export_type` | `str` | `"json"` | Export format: `"json"` or `"csv"` |
| `timeout` | `int` | `10` | HTTP timeout in seconds |
| `cookie` | `str \| None` | `None` | Full TradingView cookie string; falls back to `TRADINGVIEW_COOKIE` |

## API

### 1) `list_saved_scripts()`

Returns your own saved Pine scripts.

```python
result = pine.list_saved_scripts()
```

Output example:

```python
{
    "status": "success",
    "data": [
        {
            "id": "USER;cf7b5c71264f45ccb4d298d9ec1eaf88",
            "name": "My script",
            "version": "7.0",
            "modified": 1774357749,
        }
        ...(other scripts)
    ],
    "metadata": {},
    "error": None,
}
```


---

### 2) `get_script(pine_id, version)`

Fetches a saved Pine script (including source code) using the script id and version.

```python
result = pine.get_script(
    pine_id="USER;495ddbc28fe44ad79b3c2e1dd19eefb6",
    version="5.0",
)
```

Output example:

```python
{
    "status": "success",
    "data": {
        "id": "USER;495ddbc28fe44ad79b3c2e1dd19eefb6",
        "name": "smitrsi",
        "title": "smitrsi",
        "version": "5.0",
        "last_version": "5.0",
        "created": "2026-04-02T17:01:57.997843Z",
        "updated": "2026-04-02T17:01:57.997843Z",
        "source": "//@version=6\nindicator(\"smitrsi\")...",
        "extra": {
            "kind": "study"
        }
    },
    "metadata": {
        "pine_id": "USER;495ddbc28fe44ad79b3c2e1dd19eefb6",
        "version": "5.0"
    },
    "error": None,
}
```

Notes:

- Use `list_saved_scripts()` to get valid `id` and `version` pairs.
- This endpoint requires cookie authentication.

---

### 3) `validate_script(source)`

Validates Pine code through TradingView compiler endpoint.

```python
source_code = """
//@version=6
indicator("My Script")
plot(close)
"""

result = pine.validate_script(source_code)
```

Output example (no errors):

```python
{
    "status": "success",
    "data": None,
    "metadata": {
        "source": "//@version=6\nindicator(\"My Script\")\nplot(close)"
    },
    "error": None,
}
```

Output example (warnings only):

```python
{
    "status": "success",
    "data": None,
    "metadata": {
        "source": "//@version=6\nindicator(\"My Script\")\nplot(close)",
        "warnings": [
            {
                "message": "Some compiler warning"
            }
        ]
    },
    "error": None,
}
```

Output example (validation errors):

```python
{
    "status": "failed",
    "data": None,
    "metadata": {
        "errors": [
            {
                "message": "\"sdf\" is not a valid statement.",
                "start": {"line": 8, "column": 1},
                "end": {"line": 8, "column": 3}
            }
        ],
        "warnings": []
    },
    "error": "Pine script validation failed.",
}
```

Notes:

- Use this method when you want compiler diagnostics only.
- This method is optional before create/edit because create/edit already validate internally.

---

### 4) `create_script(name, source)`

Creates a new Pine script.

```python
source_code = """
//@version=6
indicator("My Script")
plot(close)
"""

result = pine.create_script(
    name="My Script",
    source=source_code,
)
```

Output example:

```python
{
    "status": "success",
    "data": {
        "id": "USER;cf7b5c71264f45ccb4d298d9ec1eaf88",
        "name": "My Script",
        "warnings": []
    },
    "metadata": {
        "name": "My Script",
        "source": "//@version=6\nindicator(\"My Script\")\nplot(close)"
    },
    "error": None,
}
```

Important behavior:

- `create_script` validates source internally before saving.
- If compiler returns errors, create stops and returns failed response.
- If compiler returns warnings only, create continues and warnings appear in `data["warnings"]`.

---

### 5) `edit_script(pine_id, name, source)`

Edits an existing Pine script.

```python
updated_source = """
//@version=6
indicator("My Script v2")
plot(close)
"""

result = pine.edit_script(
    pine_id="USER;cf7b5c71264f45ccb4d298d9ec1eaf88",
    name="My Script v2",
    source=updated_source,
)
```

Output example:

```python
{
    "status": "success",
    "data": {
        "id": "USER;cf7b5c71264f45ccb4d298d9ec1eaf88",
        "name": "My Script v2",
        "warnings": []
    },
    "metadata": {
        "pine_id": "USER;cf7b5c71264f45ccb4d298d9ec1eaf88",
        "name": "My Script v2",
        "source": "//@version=6\nindicator(\"My Script v2\")\nplot(close)"
    },
    "error": None,
}
```

Important behavior:

- `edit_script` validates source internally before saving.
- If validation fails, edit is blocked.
- Warnings are returned in `data["warnings"]` when save succeeds.

---

### 6) `delete_script(pine_id)`

Deletes a script by Pine ID.

```python
result = pine.delete_script("USER;cf7b5c71264f45ccb4d298d9ec1eaf88")
```

Output example:

```python
{
    "status": "success",
    "data": {
        "id": "USER;cf7b5c71264f45ccb4d298d9ec1eaf88",
        "deleted": True
    },
    "metadata": {
        "pine_id": "USER;cf7b5c71264f45ccb4d298d9ec1eaf88"
    },
    "error": None,
}
```

Notes:

- Delete uses a POST request with no payload.
- TradingView returns `"ok"` on success.

---

## Error Format

All Pine methods use the standard envelope for failures:

```python
{
    "status": "failed",
    "data": None,
    "metadata": {},
    "error": "TradingView cookie is required for Pine Script operations...",
}
```

Metadata behavior summary:

- `list_saved_scripts()` returns empty metadata.
- `list_saved_scripts()` `data` items include `id`, `name`, `version`, and `modified`.
- All other Pine methods return input parameters inside metadata.
