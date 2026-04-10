# Pine Scraper

## Overview

The Pine scraper manages authenticated TradingView Pine Script operations through the Pine facade API.

Public methods:

- `list_saved_scripts()`
- `validate_script(source)`
- `get_script(pine_id, version)`
- `create_script(name, source)`
- `edit_script(pine_id, name, source)`
- `delete_script(pine_id)`

All public methods are decorated with `catch_errors` and return the standardized response envelope.

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

| Parameter | Type | Default | Behavior |
|---|---|---|---|
| `export_result` | `bool` | `False` | Enables export when a method supports export. |
| `export_type` | `str` | `"json"` | Export format (`"json"` or `"csv"`). |
| `timeout` | `int` | `10` | HTTP timeout in seconds. |
| `cookie` | `str \| None` | `None` | TradingView cookie. If `None`, falls back to `TRADINGVIEW_COOKIE` environment variable. |

## Cookie-Required Behavior

All Pine public methods call `_validate_cookie_required()` before making network calls.

- If `self.cookie` is truthy, execution continues.
- If cookie is missing (including empty string), the method returns failed status with this message:

```text
TradingView cookie is required for Pine Script operations. Provide it via the cookie argument or TRADINGVIEW_COOKIE environment variable.
```

Headers for Pine facade requests are built by `_build_pine_headers()` and include:

- `User-Agent` (from `BaseScraper`)
- `cookie`
- `accept: */*`
- `origin: https://in.tradingview.com`
- `referer: https://in.tradingview.com/`

## Response Envelope Semantics

All methods return this shape:

```python
{
    "status": "success" | "failed",
    "data": <payload or None>,
    "metadata": <dict>,
    "error": None | "message",
}
```

Metadata semantics come from `catch_errors` + base response helpers:

- `catch_errors` captures method arguments into `metadata` before method execution.
- Captured metadata excludes `self` and arguments whose value is `None`.
- `_success_response()` and `_error_response()` merge additional metadata into captured metadata.
- Unexpected exceptions are converted to failed envelopes with `error = "Unexpected error: ..."`.
- `create_script` and `edit_script` restore outer metadata after internal `validate_script` calls so final metadata reflects outer call arguments.

## Endpoint Behavior

Base URL: `https://pine-facade.tradingview.com/pine-facade`

| Method | HTTP | Endpoint | Request details | Success expectation |
|---|---|---|---|---|
| `list_saved_scripts` | GET | `/list` | Query params: `filter=saved` | Parsed JSON payload must be a list |
| `validate_script` | POST | `/translate_light` | Query params: `v=3`; multipart field `source` | Parsed JSON payload must be a dict with dict `result` |
| `get_script` | GET | `/get/{pine_id}/{version}` | `pine_id` and `version` are URL-encoded path segments | Parsed JSON payload must be a dict |
| `create_script` | POST | `/save/new` | Query params: `name`, `allow_overwrite=true`; multipart field `source` | Parsed JSON payload must include `result.metaInfo.scriptIdPart` |
| `edit_script` | POST | `/save/next/{pine_id}` | URL-encoded `pine_id`; query params: `allow_create_new=false`, `name`; multipart field `source` | Parsed JSON payload must include `result.metaInfo.scriptIdPart` |
| `delete_script` | POST | `/delete/{pine_id}` | URL-encoded `pine_id`; no body | Parsed JSON value must equal string `"ok"` |

Notes:

- Path values are encoded via `quote(value, safe="")`.
- `_request()` always parses responses using `response.json()`.

## Validation Flow

### Shared validators

- `_validate_cookie_required()`
- `_validate_non_empty(value, field_name)` (whitespace-only values are treated as empty)

### Per-method sequence

1. `list_saved_scripts()`
- Cookie check.

2. `validate_script(source)`
- Cookie check.
- Source non-empty check.
- Payload must be dict.
- `payload["result"]` must be dict.

3. `get_script(pine_id, version)`
- Cookie check.
- `pine_id` non-empty check.
- `version` non-empty check.
- Payload must be dict.
- Mapped details must include string `source`.

4. `create_script(name, source)`
- Cookie check.
- `name` non-empty check.
- `source` non-empty check.
- Internal `validate_script(source)` call.
- If validation fails, create returns failed and does not call save endpoint.
- Save payload must include `result.metaInfo.scriptIdPart`.

5. `edit_script(pine_id, name, source)`
- Cookie check.
- `pine_id` non-empty check.
- `name` non-empty check.
- `source` non-empty check.
- Internal `validate_script(source)` call.
- If validation fails, edit returns failed and does not call save endpoint.
- Save payload must include `result.metaInfo.scriptIdPart`.

6. `delete_script(pine_id)`
- Cookie check.
- `pine_id` non-empty check.
- Parsed response must equal `"ok"`.

## Public Methods

### 1) `list_saved_scripts()`

Returns saved scripts for the authenticated account.

Mapped item shape:

```python
{
    "id": item.get("scriptIdPart", ""),
    "name": item.get("scriptName") or item.get("scriptTitle", ""),
    "version": item.get("version") or item.get("scriptVersion"),
    "modified": <non-negative int, else 0>,
}
```

If `export_result=True`, this method exports with:

- `symbol="pine_saved_scripts"`
- `data_category="pine"`

Success example:

```python
{
    "status": "success",
    "data": [
        {
            "id": "USER;abc123",
            "name": "My Script",
            "version": "4",
            "modified": 1700000000,
        }
    ],
    "metadata": {},
    "error": None,
}
```

### 2) `validate_script(source)`

Validates Pine source through the translate endpoint.

Behavior:

- `errors` non-empty -> failed response with `error="Pine script validation failed."`; `errors` and `warnings` are placed in metadata.
- `errors` empty and `warnings` non-empty -> success response, `data=None`, warnings in metadata.
- both empty -> success response, `data=None`.

Warnings-only success example:

```python
{
    "status": "success",
    "data": None,
    "metadata": {
        "source": "//@version=6\nvar x = na",
        "warnings": [{"text": "Unused variable"}],
    },
    "error": None,
}
```

Compiler-error failure example:

```python
{
    "status": "failed",
    "data": None,
    "metadata": {
        "source": "//@version=6\nundefined()",
        "errors": [{"text": "Undefined function"}],
        "warnings": [],
    },
    "error": "Pine script validation failed.",
}
```

### 3) `get_script(pine_id, version)`

Fetches one script and maps:

```python
{
    "id": <payload scriptIdPart or input pine_id>,
    "name": <scriptName or scriptTitle or "">,
    "title": <scriptTitle or scriptName>,
    "version": <payload version or input version>,
    "last_version": payload.get("lastVersionMaj"),
    "created": payload.get("created"),
    "updated": payload.get("updated"),
    "source": <required string>,
    "extra": <dict, defaults to {}>,
}
```

If `export_result=True`, this method exports with:

- `symbol=<pine_id>`
- `data_category="pine_script"`

### 4) `create_script(name, source)`

Creates a script after internal `validate_script(source)` succeeds.

Success data shape:

```python
{
    "id": script_result.get("scriptIdPart", ""),
    "name": script_result.get("shortDescription")
        or script_result.get("description")
        or name,
    "warnings": <validation warnings list or []>,
}
```

Behavior details:

- Validation warnings do not block create.
- Validation errors block create.
- When validation fails, response metadata includes outer args (`name`, `source`) and forwards validation `errors`/`warnings` into metadata.

### 5) `edit_script(pine_id, name, source)`

Edits a script after internal `validate_script(source)` succeeds.

Success data shape:

```python
{
    "id": script_result.get("scriptIdPart", "") or pine_id,
    "name": script_result.get("shortDescription")
        or script_result.get("description")
        or name,
    "warnings": <validation warnings list or []>,
}
```

Behavior details:

- Validation warnings do not block edit.
- Validation errors block edit.
- When validation fails, response metadata includes outer args (`pine_id`, `name`, `source`) and forwards validation `errors`/`warnings` into metadata.

### 6) `delete_script(pine_id)`

Deletes a script by ID.

Success response:

```python
{
    "status": "success",
    "data": {"id": "USER;test123"},
    "metadata": {"pine_id": "USER;test123"},
    "error": None,
}
```

Failure behavior:

- If parsed response is not exactly `"ok"`, returns failed status with:

```text
Pine delete endpoint returned unexpected response: <response>
```

Important:

- Success data contains only `id`; there is no `deleted` field.

## Warning and Error Metadata Matrix

| Method | Success metadata behavior | Failure metadata behavior |
|---|---|---|
| `list_saved_scripts` | Usually `{}` (no method args) | Usually `{}` unless decorator-level metadata is present |
| `validate_script` | Includes `source`; includes `warnings` when present | Includes `source`; compiler failures include `errors` and `warnings` |
| `get_script` | Includes `pine_id`, `version` | Includes `pine_id`, `version` |
| `create_script` | Includes `name`, `source`; warnings are in `data["warnings"]` | Includes `name`, `source`; validation failure may include `errors`/`warnings` |
| `edit_script` | Includes `pine_id`, `name`, `source`; warnings are in `data["warnings"]` | Includes `pine_id`, `name`, `source`; validation failure may include `errors`/`warnings` |
| `delete_script` | Includes `pine_id` | Includes `pine_id` |

## Known Edge Behavior

`delete_script` depends on JSON parsing in `_request()` and only succeeds when parsed response equals `"ok"`.

- If the endpoint returns non-JSON plain text `ok`, `_request()` returns parse failure.
- If the endpoint returns JSON but not `"ok"`, delete returns failed status.
