# API Conventions

This document defines the standards for the `tv_scraper` public API.

## Input Parameters

### Symbol Identification
All scrapers accept `exchange` and `symbol` as **separate** string parameters:
```python
scraper.get_data(exchange="NASDAQ", symbol="AAPL")
```

### Field Selection
Optional field selection uses a list of strings:
```python
scraper.get_data(exchange="NASDAQ", symbol="AAPL", fields=["close", "volume", "change"])
```

### Sorting
Sorting follows a consistent pattern:
```python
scraper.get_data(sort_by="volume", sort_order="desc")  # or "asc"
```
`sort_order` defaults to `"desc"` when not specified.

### Naming Convention
All parameters use **snake_case**:
```python
# Correct
scraper.get_data(export_result=True, export_type="json", sort_by="change")

# Wrong — never use camelCase
scraper.get_data(exportResult=True)
```

## Output Format

### Response Envelope
Every public scraper method returns a standardized response dict:

```python
{
    "status": "success",        # or "failed"
    "data": [...],              # payload (list, dict, or None on failure)
    "metadata": {               # contextual info
        "symbol": "AAPL",
        "exchange": "NASDAQ",
        "total": 25
    },
    "error": None               # error message string, or None on success
}
```

### Success Response
- `status` is always `"success"`
- `data` contains the requested payload
- `error` is always `None`
- `metadata` contains relevant context (symbol, exchange, counts, etc.)

### Error Response
- `status` is always `"failed"`
- `data` is always `None`
- `error` contains a descriptive error message
- `metadata` may contain partial context

## Error Handling

### Scraper Methods Never Raise
Public scraper methods **never raise exceptions**. All errors are caught internally and returned as error responses:

```python
result = scraper.get_data(exchange="INVALID", symbol="AAPL")
# Returns: {"status": "failed", "data": None, "error": "Invalid exchange: ...", "metadata": {}}
```

### Validators Raise Internally
The `DataValidator` raises `ValidationError` for invalid input. `BaseScraper` subclasses catch these and convert them to error responses — exceptions never escape to user code.

## Type Hints

All functions and methods have **100% type hints**:
```python
def get_data(
    self,
    exchange: str,
    symbol: str,
    fields: Optional[List[str]] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "desc",
) -> Dict[str, Any]:
    ...
```

## Docstrings

All public classes and methods use **Google-style docstrings**:
```python
def validate_exchange(self, exchange: str) -> bool:
    """Validate exchange exists.

    Args:
        exchange: Exchange name to validate.

    Returns:
        True if exchange is valid.

    Raises:
        ValidationError: If exchange is not found.
    """
```
