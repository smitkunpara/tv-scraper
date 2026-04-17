# Pine

!!! info "Version Note"
    `list_saved_scripts()` includes each script `version` in the returned data as of `1.2.1`.

`Pine` manages authenticated Pine Script operations through the TradingView Pine facade.

## Cookie Required

Every public `Pine` method requires a TradingView cookie.

```python
from tv_scraper import Pine

pine = Pine(cookie="paste_your_cookie_here")
```

If the cookie is missing, the method returns a failed response instead of making the request.

## Quick Use

### List saved scripts

```python
result = pine.list_saved_scripts()
```

#### Output structure (truncated)

```python
{
    "status": "success",
    "data": [
        {
            "id": "USER;abc123",
            "name": "My Script",
            "version": "5.0",
            "modified": 1700000000,
        },
        ...
    ],
    "metadata": {},
    "warnings": [],
    "error": None,
}
```

### Validate source

```python
result = pine.validate_script(source="//@version=6\nindicator('Demo')\nplot(close)")
```

#### Output structure (warnings-only success)

```python
{
    "status": "success",
    "data": None,
    "metadata": {
        "source": "//@version=6\nvar x = na",
    },
    "warnings": [{"text": "Unused variable"}],
    "error": None,
}
```

!!! info "Warning Behavior"
    All Pine methods now use a standardized top-level `warnings` field:
    - `validate_script()`, `create_script()`, and `edit_script()` return compiler warnings in the top-level `warnings` field.

### Create a script

```python
result = pine.create_script(
    name="My Script",
    source="//@version=6\nindicator('Demo')\nplot(close)",
)
```

#### Output structure

```python
{
    "status": "success",
    "data": {
        "id": "USER;abc123",
        "name": "My Script",
    },
    "metadata": {
        "name": "My Script",
        "source": "//@version=6\nindicator('Demo')\nplot(close)",
    },
    "warnings": [],
    "error": None,
}
```

### Edit a script

```python
result = pine.edit_script(
    pine_id="USER;abc123",
    name="My Script",
    source="//@version=6\nindicator('Demo 2')\nplot(close)",
)
```

#### Output structure

```python
{
    "status": "success",
    "data": {
        "id": "USER;abc123",
        "name": "My Script",
    },
    "metadata": {
        "pine_id": "USER;abc123",
        "name": "My Script",
        "source": "//@version=6\nindicator('Demo 2')\nplot(close)",
    },
    "warnings": [],
    "error": None,
}
```

### Fetch script content

```python
result = pine.get_script(pine_id="USER;abc123", version="5.0")
```

#### Output structure

```python
{
    "status": "success",
    "data": {
        "id": "USER;abc123",
        "name": "My Script",
        "title": "My Script",
        "version": "5.0",
        "last_version": 6,
        "created": 1700000000,
        "updated": 1700000500,
        "source": "//@version=6\nindicator('Demo')\nplot(close)",
        "extra": {},
    },
    "metadata": {
        "pine_id": "USER;abc123",
        "version": "5.0",
    },
    "warnings": [],
    "error": None,
}
```

### Delete a script

```python
result = pine.delete_script(pine_id="USER;abc123")
```

#### Output structure

```python
{
    "status": "success",
    "data": {"id": "USER;abc123"},
    "metadata": {"pine_id": "USER;abc123"},
    "warnings": [],
    "error": None,
}
```

!!! failure "wrong input"
    This fails because the source is empty.

    ```python
    pine.validate_script(source="   ")
    ```

!!! note "Notes"
    - `create_script()` and `edit_script()` run `validate_script()` internally before saving.
    - `get_script()` returns the raw Pine source plus metadata such as `title`, `version`, `created`, and `updated`.
    - `delete_script()` succeeds only when the Pine endpoint returns the expected `"ok"` value.
