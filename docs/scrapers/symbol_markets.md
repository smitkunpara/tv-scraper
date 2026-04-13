# Symbol Markets

`SymbolMarkets` helps you find where a symbol is traded across TradingView scanners.

## Quick Use

```python
from tv_scraper import SymbolMarkets

scraper = SymbolMarkets()
result = scraper.get_symbol_markets(symbol="AAPL")
```

Output structure:

```python
{
    "status": "success",
    "data": [
        {
            "symbol": "NASDAQ:AAPL",
            "name": "AAPL",
            "close": 150.25,
            "exchange": "NASDAQ",
            "type": "stock",
            "currency": "USD",
        },
        ...
    ],
    "metadata": {
        "symbol": "AAPL",
        "scanner": "global",
        "total": 14,
        "total_available": 14,
        ...
    },
    "error": None,
}
```

You can also pass an exchange-prefixed symbol:

```python
result = scraper.get_symbol_markets(symbol="NASDAQ:AAPL")
```

Output structure:

```python
{
    "status": "success",
    "data": [
        {
            "symbol": "NASDAQ:AAPL",
            "name": "AAPL",
            "close": 150.25,
            "exchange": "NASDAQ",
        },
        ...
    ],
    "metadata": {
        "symbol": "NASDAQ:AAPL",
        "scanner": "global",
        "total": 14,
        "total_available": 14,
        ...
    },
    "error": None,
}
```

The scraper uses only the part after `:` for matching.

## Inputs

| Parameter | Accepted values |
|-----------|-----------------|
| `symbol` | plain symbol or `EXCHANGE:SYMBOL` |
| `scanner` | `global`, `america`, `crypto`, `forex`, `cfd` |
| `limit` | `1` to `1000` |
| `fields` | optional field list |

!!! failure "wrong input"
    Older examples sometimes use the wrong method name. This is wrong:

    ```python
    scraper.get_markets(symbol="AAPL")
    ```

    Use:

    ```python
    scraper.get_symbol_markets(symbol="AAPL")
    ```

!!! note "Notes"
    - If no rows are found, the method returns `status="failed"`.
    - Metadata keeps your original `symbol` input, even when the search uses the part after `:`.
