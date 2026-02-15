# Options

## Overview

The `Options` scraper retrieves option chain data for a given underlying symbol via the TradingView options scanner API. It supports fetching chains filtered by either expiration date or strike price.

## Quick Start

```python
from tv_scraper.scrapers.market_data import Options

scraper = Options()

# Get option chain by expiration date
result = scraper.get_chain_by_expiry(
    exchange="BSE",
    symbol="SENSEX",
    expiration=20260219,
    root="BSX"
)
print(result["data"])

# Get option chain by strike price
result = scraper.get_chain_by_strike(
    exchange="BSE",
    symbol="SENSEX",
    strike=83300
)
```

## Constructor

```python
Options(
    export_result: bool = False,
    export_type: str = "json",   # "json" or "csv"
    timeout: int = 10,
)
```

## Methods

### `get_chain_by_expiry(exchange, symbol, expiration, root, columns=None)`

Fetch the option chain for a specific expiration date.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `exchange` | `str` | — | Exchange name (e.g. `"BSE"`) |
| `symbol` | `str` | — | Underlying symbol (e.g. `"SENSEX"`) |
| `expiration` | `int` | — | Expiry date in YYYYMMDD format (e.g. `20260219`) |
| `root` | `str` | — | Root symbol for the option (e.g. `"BSX"`) |
| `columns` | `list[str] \| None` | `None` | Specific data columns to retrieve. |

### `get_chain_by_strike(exchange, symbol, strike, columns=None)`

Fetch options across all expirations for a specific strike price.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `exchange` | `str` | — | Exchange name (e.g. `"BSE"`) |
| `symbol` | `str` | — | Underlying symbol (e.g. `"SENSEX"`) |
| `strike` | `int \| float` | — | Strike price (e.g. `83300`) |
| `columns` | `list[str] \| None` | `None` | Specific data columns to retrieve. |

## Default Columns

If `columns` is not specified, the following fields are retrieved:

`ask`, `bid`, `currency`, `delta`, `expiration`, `gamma`, `iv`, `option-type`, `pricescale`, `rho`, `root`, `strike`, `theoPrice`, `theta`, `vega`, `bid_iv`, `ask_iv`

## Response Format

Returns a standardized response envelope:

```json
{
    "status": "success",
    "data": [
        {
            "symbol": "BSE:BSX260219C83300",
            "ask": 251.5,
            "bid": 250.05,
            "currency": "INR",
            "delta": 0.30031253196887614,
            "expiration": 20260219,
            "gamma": 0.0002619084231041657,
            "iv": 0.12206886452622712,
            "option-type": "call",
            "pricescale": 100,
            "rho": 4.260193630531909,
            "root": "BSX",
            "strike": 83300,
            "theoPrice": 251.05,
            "theta": -36.46051324424114,
            "vega": 37.841028744369176,
            "bid_iv": 0.12179930401016525,
            "ask_iv": 0.12218255530179331
        },
        ...(other objects)
    ],
    "metadata": {
        "exchange": "BSE",
        "symbol": "SENSEX",
        "filter_type": "expiry",
        "filter_value": 20260219,
        "total": 14
    },
    "error": null
}
```
