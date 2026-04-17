# Technicals

`Technicals` fetches scanner-based indicator values for one `exchange:symbol`.

## Quick Use

### Selected indicators

```python
from tv_scraper import Technicals

scraper = Technicals()
result = scraper.get_technicals(
    exchange="NASDAQ",
    symbol="AAPL",
    timeframe="1d",
    technical_indicators=["RSI", "MACD.macd"],
)
```

#### Output structure

```python
{
    "status": "success",
    "data": {
        "RSI": 54.36791522625663,
        "MACD.macd": -1.7690915227776713,
    },
    "metadata": {
        "exchange": "NASDAQ",
        "symbol": "AAPL",
        "timeframe": "1d",
        "technical_indicators": ["RSI", "MACD.macd"],
    },
    "warnings": [],
    "error": None,
}
```

### All indicators

```python
result = scraper.get_technicals(
    exchange="NASDAQ",
    symbol="AAPL",
    timeframe="1d"
)
```

#### Output structure (truncated)

```python
{
    "status": "success",
    "data": {
        "Recommend.Other": 0.09090909090909091,
        "Recommend.All": 0.3787878787878788,
        "RSI": 54.36791522625663,
        "MACD.macd": -1.7690915227776713,
        "MACD.signal": -2.9115386038865543,
        ...
    },
    "metadata": {
        "exchange": "NASDAQ",
        "symbol": "AAPL",
        "timeframe": "1d",
    },
    "warnings": [],
    "error": None,
}
```

## Inputs

| Parameter | Notes |
|-----------|-------|
| `exchange` | Use a supported exchange from [Exchanges](../supported_data.md#exchanges) |
| `symbol` | Symbol slug such as `AAPL` |
| `timeframe` | Use a supported timeframe from [Timeframes](../supported_data.md#timeframes) |
| `technical_indicators` | Use supported values from [Technical indicators](../supported_data.md#technical-indicators). If `None` (default), all indicators are returned; otherwise only the requested names are returned. |

!!! failure "wrong input"
    This fails because `technical_indicators` must contain supported names.

    ```python
    scraper.get_technicals(
        exchange="NASDAQ",
        symbol="AAPL",
        technical_indicators=["INVALID_XYZ"],
    )
    ```

!!! note "Notes"
    - If `technical_indicators` is `None` (or omitted), the method requests the full indicator set.
    - If `technical_indicators` is a list, only those indicator names are returned in `data`.
    - Missing indicator values come back as `None` instead of forcing failure.
    - Daily requests use plain indicator keys; non-daily requests still return plain keys after internal suffix cleanup.
