# Pine Scraper

## Overview

The Pine scraper provides authenticated TradingView Pine script management APIs.

Current support includes:

- View your saved Pine scripts
- Validate Pine source code
- Create new scripts
- Edit existing scripts
- Delete scripts

Cookie authentication is required for all Pine operations.

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
            "modified": 1774357749,
        }
        ...(other scripts)
    ],
    "metadata": {},
    "error": None,
}
```


---

### 2) `validate_script(source)`

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

### 3) `create_script(name, source)`

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

### 4) `edit_script(pine_id, name, source)`

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

### 5) `delete_script(pine_id)`

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
- All other Pine methods return input parameters inside metadata.
