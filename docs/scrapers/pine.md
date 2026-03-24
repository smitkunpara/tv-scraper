# Pine Scraper

## Overview

The Pine scraper provides authenticated access to TradingView Pine endpoints. In this first iteration, it supports listing your saved Pine scripts.

Cookie authentication is mandatory for all Pine operations.

## Import

```python
from tv_scraper.scrapers.scripts import Pine
```

## Constructor

```python
Pine(
    export_result: bool = False,
    export_type: str = "json",
    timeout: int = 10,
    cookie: str | None = None,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `export_result` | `bool` | `False` | Whether to export results to a file |
| `export_type` | `str` | `"json"` | Export format: `"json"` or `"csv"` |
| `timeout` | `int` | `10` | HTTP request timeout in seconds |
| `cookie` | `str \| None` | `None` | Full TradingView cookie string. Falls back to `TRADINGVIEW_COOKIE` env var |

## Methods

### `list_saved_scripts`

```python
list_saved_scripts() -> dict[str, Any]
```

Fetch your own saved Pine scripts from TradingView.

### Output Fields

Each item in `data` contains only:

- `id`
- `name`
- `modified`

## Response Format

```python
{
    "status": "success",
    "data": [
        {
            "id": "USER;cf7b5c71264f45ccb4d298d9ec1eaf88",
            "name": "My scrip test",
            "modified": 1774357749,
        }
    ],
    "metadata": {
        "total": 1,
        "filter": "saved",
    },
    "error": None,
}
```

## Example

```python
import os
from tv_scraper.scrapers.scripts import Pine

pine = Pine(cookie=os.environ.get("TRADINGVIEW_COOKIE"))
result = pine.list_saved_scripts()

if result["status"] == "success":
    for script in result["data"]:
        print(script["id"], script["name"], script["modified"])
else:
    print(result["error"])
```

## Errors

If cookie is missing:

```python
{
    "status": "failed",
    "data": None,
    "metadata": {},
    "error": "TradingView cookie is required for Pine Script operations...",
}
```
