# Pine Scraper

## Overview

The Pine scraper provides authenticated access to TradingView Pine endpoints. It currently supports:

- Listing your saved Pine scripts
- Validating Pine source code
- Creating new Pine scripts
- Editing existing Pine scripts
- Deleting existing Pine scripts
- Creating scripts from a local file path

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

### `validate_script`

```python
validate_script(source: str) -> dict[str, Any]
```

Validates Pine source via `translate_light?v=3` before create/edit operations.

If validation has warnings, they are returned under `metadata["warnings"]` and logged.

If validation has errors, response status is `failed` and errors are included in `metadata["errors"]`.

### `create_script`

```python
create_script(name: str, source: str, allow_overwrite: bool = True) -> dict[str, Any]
```

Creates a new script using `save/new` endpoint.

Create flow:

1. Validate source (`validate_script`)
2. Stop if validation has errors
3. Continue with create request when warnings or no warnings

For `create_script` and `edit_script`, compiler warnings are returned in the success `data` under `data["warnings"]`.
These responses return `id`, `name`, and `warnings` in `data`.
The `modified` field is returned by `list_saved_scripts` items.

### `edit_script`

```python
edit_script(pine_id: str, name: str, source: str) -> dict[str, Any]
```

Edits an existing script using `save/next/{pine_id}` with query params:

- `allow_create_new=false`
- `name=<script-name>`

Edit flow:

1. Validate source (`validate_script`)
2. Stop if validation has errors
3. Continue with edit request when warnings or no warnings

### `create_script_from_file`

```python
create_script_from_file(
    file_path: str,
    name: str,
    allow_overwrite: bool = True,
) -> dict[str, Any]
```

Reads a UTF-8 text file from disk, validates it, then creates a new Pine script.

Binary/object files are rejected.

### `delete_script`

```python
delete_script(pine_id: str) -> dict[str, Any]
```

Deletes an existing script using `POST /pine-facade/delete/{pine_id}`.

The endpoint has no request payload. Successful response body is the string `"ok"`.

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

For create/edit success, metadata echoes input values (for example `name`, `pine_id`, `allow_overwrite`) and warnings are returned in `data["warnings"]`.

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

source_code = """
//@version=6
indicator(\"My Script\")
plot(close)
"""

validation = pine.validate_script(source_code)
print("Warnings:", validation["metadata"].get("warnings", []))

if validation["status"] == "success":
    created = pine.create_script(name="My Script", source=source_code)
    print(created)

edited = pine.edit_script(
    pine_id="USER;cf7b5c71264f45ccb4d298d9ec1eaf88",
    name="My Script v2",
    source=source_code,
)
print(edited)

deleted = pine.delete_script("USER;cf7b5c71264f45ccb4d298d9ec1eaf88")
print(deleted)

created_from_file = pine.create_script_from_file(
    file_path="./my_script.pine",
    name="My Script From File",
)
print(created_from_file)

# Optional interactive flow
file_path = input("Enter source file path: ").strip()
script_name = input("Enter script name: ").strip()
script_type = input("Enter type (indicator/strategy/library): ").strip()
print("Script type selected:", script_type)
print(pine.create_script_from_file(file_path=file_path, name=script_name))
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
