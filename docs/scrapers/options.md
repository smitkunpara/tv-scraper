# Options

!!! info "Version Note"
    The options API has been unified around `get_options(...)`. Use this single method for expiry-only, strike-only, or combined filtering.

`Options` fetches option-chain rows for one underlying symbol.

## Quick Use

### By expiration

```python
from tv_scraper import Options

scraper = Options()
result = scraper.get_options(
    exchange="BSE",
    symbol="SENSEX",
    expiration=20260219,
)
```

#### Output structure

```python
{
    "status": "success",
    "data": [
        {
            "symbol": "BSE:OPTION_SYMBOL",
            "expiration": 20260219,
            "strike": 83300,
            "bid": 101.5,
            "ask": 103.0,
        },
        ...,
    ],
    "metadata": {
        "exchange": "BSE",
        "symbol": "SENSEX",
        "expiration": 20260219,
        "total": 84,
        "filter_value": 20260219,
    },
    "warnings": [],
    "error": None,
}
```

### By strike

```python
result = scraper.get_options(
    exchange="BSE",
    symbol="SENSEX",
    strike=83300,
)
```

#### Output structure

```python
{
    "status": "success",
    "data": [
        {
            "symbol": "BSE:OPTION_SYMBOL",
            "strike": 83300,
            "bid": 101.5,
            "ask": 103.0,
        },
        ...,
    ],
    "metadata": {
        "exchange": "BSE",
        "symbol": "SENSEX",
        "strike": 83300,
        "total": 12,
        "filter_value": 83300,
    },
    "warnings": [],
    "error": None,
}
```

### By expiration and strike

```python
result = scraper.get_options(
    exchange="BSE",
    symbol="SENSEX",
    expiration=20260219,
    strike=83300,
    columns=["strike", "bid", "ask", "iv"],
)
```

#### Output structure

```python
{
    "status": "success",
    "data": [
        {
            "symbol": "BSE:OPTION_SYMBOL",
            "strike": 83300,
            "bid": 101.5,
            "ask": 103.0,
            "iv": 18.4,
        }
    ],
    "metadata": {
        "exchange": "BSE",
        "symbol": "SENSEX",
        "expiration": 20260219,
        "strike": 83300,
        "columns": ["strike", "bid", "ask", "iv"],
        "total": 1,
        "filter_value": {"expiration": 20260219, "strike": 83300},
    },
    "warnings": [],
    "error": None,
}
```

## Inputs

| Parameter | Notes |
|-----------|-------|
| `exchange` | underlying exchange, such as `BSE` |
| `symbol` | underlying symbol, such as `SENSEX` |
| `expiration` | optional `YYYYMMDD` integer |
| `strike` | optional `int` or `float` |
| `columns` | optional list from the allowed option columns below |

At least one of `expiration` or `strike` is required.

### Allowed option columns

`ask`, `bid`, `currency`, `delta`, `expiration`, `gamma`, `iv`, `option-type`, `pricescale`, `rho`, `root`, `strike`, `theoPrice`, `theta`, `vega`, `bid_iv`, `ask_iv`

!!! failure "wrong input"
    This fails because the request has no filter.

    ```python
    scraper.get_options(exchange="BSE", symbol="SENSEX")
    ```

!!! note "Notes"
    - `expiration` is validated as a real calendar date, not just an 8-digit number.
    - If TradingView has no option chain for the symbol, the method returns `status="failed"` with a chain-not-found style message.
