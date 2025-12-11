# Supported Data

## Overview

This document provides comprehensive information about all supported data types in the TradingView Scraper. It serves as a central reference for areas, exchanges, indicators, languages, news providers, and timeframes that the system can handle.

## Why This Feature Exists

The supported data documentation exists to:

- Provide a single source of truth for all available data options
- Help developers understand what data they can work with
- Ensure consistency across different modules and features
- Serve as a reference for validation and error handling
- Enable proper parameter usage in API calls and scraping operations

## Supported Areas

The system supports geographic areas that can be used for filtering news and market data.

### Area Codes and Meanings

| Area Code | Full Name | Description |
|-----------|-----------|-------------|
| `WLD` | World | Global coverage |
| `AME` | Americas | North and South America |
| `EUR` | Europe | European continent |
| `ASI` | Asia | Asian continent |
| `OCN` | Oceania | Australia, New Zealand, Pacific Islands |
| `AFR` | Africa | African continent |

### Usage Example

```python
# Filter news by area
news_scraper.scrape_headlines(
    symbol='BTCUSD',
    exchange='BINANCE',
    area='americas',  # Use the lowercase key from areas.json
    sort='latest'
)
```

## Supported Exchanges

The system supports 260+ exchanges across various categories including cryptocurrency, forex, stocks, commodities, and indices.

### Exchange Categories

1. **Cryptocurrency Exchanges**: BINANCE, COINBASE, KRAKEN, BITFINEX, etc.
2. **Forex Brokers**: OANDA, FOREXCOM, FXCM, PEPPERSTONE, etc.
3. **Stock Exchanges**: NASDAQ, NYSE, LSE, TSE, HKEX, etc.
4. **Commodities Exchanges**: CME, NYMEX, COMEX, etc.
5. **Indices and Special**: INDEX, ECONOMICS, TVC, etc.

### Complete Exchange List

The full list of 260+ supported exchanges can be found in [`tradingview_scraper/data/exchanges.txt`](https://github.com/smitkunpara/tradingview-scraper/blob/main/tradingview_scraper/data/exchanges.txt). Some notable exchanges include:

- **Major Crypto**: BINANCE, BINANCEUS, COINBASE, KRAKEN, KUCOIN, BYBIT, OKX, HUOBI
- **Traditional Finance**: NASDAQ, NYSE, LSE, TSE, HKEX, SGX, EURONEXT
- **Forex**: OANDA, FOREXCOM, FXCM, PEPPERSTONE, SAXO
- **Commodities**: CME, NYMEX, COMEX, TOCOM
- **DeFi/DEX**: UNISWAP, PANCAKESWAP, SUSHISWAP, CURVE

### Usage Example

```python
# Scrape data from a specific exchange
indicators_scraper.scrape(
    exchange="BINANCE",  # Must match exactly with exchanges.txt
    symbol="BTCUSDT",
    timeframe="1d",
    indicators=["RSI", "Stoch.K"]
)
```

## Supported Indicators

The system supports 81 technical indicators covering various analysis categories.

### Indicator Categories

1. **Momentum Indicators**: RSI, Stochastic, CCI, ADX, AO
2. **Moving Averages**: EMA, SMA, VWMA, HullMA
3. **Trend Analysis**: MACD, Ichimoku, Pivot Points
4. **Volume Analysis**: BBPower, VWMA
5. **Recommendations**: Various "Recommend" indicators

### Complete Indicator List

The full list of 81 supported indicators can be found in [`tradingview_scraper/data/indicators.txt`](https://github.com/smitkunpara/tradingview-scraper/blob/main/tradingview_scraper/data/indicators.txt). Here are some key indicators:

#### Basic Indicators
- `RSI` - Relative Strength Index
- `Stoch.K` - Stochastic %K
- `Stoch.D` - Stochastic %D
- `CCI20` - Commodity Channel Index (20-period)
- `ADX` - Average Directional Index
- `AO` - Awesome Oscillator
- `Mom` - Momentum

#### Moving Averages
- `EMA10`, `EMA20`, `EMA30`, `EMA50`, `EMA100`, `EMA200`
- `SMA10`, `SMA20`, `SMA30`, `SMA50`, `SMA100`, `SMA200`
- `VWMA` - Volume Weighted Moving Average
- `HullMA9` - Hull Moving Average (9-period)

#### MACD Components
- `MACD.macd` - MACD line
- `MACD.signal` - MACD signal line

#### Pivot Points (Multiple Types)
- **Classic**: `Pivot.M.Classic.S3` through `Pivot.M.Classic.R3`
- **Fibonacci**: `Pivot.M.Fibonacci.S3` through `Pivot.M.Fibonacci.R3`
- **Camarilla**: `Pivot.M.Camarilla.S3` through `Pivot.M.Camarilla.R3`
- **Woodie**: `Pivot.M.Woodie.S3` through `Pivot.M.Woodie.R3`
- **DeMark**: `Pivot.M.Demark.S1`, `Pivot.M.Demark.Middle`, `Pivot.M.Demark.R1`

#### Recommendation Indicators
- `Recommend.Other`
- `Recommend.All`
- `Recommend.MA`
- `Rec.Stoch.RSI`
- `Rec.WR`
- `Rec.BBPower`
- `Rec.UO`
- `Rec.Ichimoku`
- `Rec.VWMA`
- `Rec.HullMA9`

### Usage Example

```python
# Scrape multiple indicators
indicators_scraper.scrape(
    exchange="BINANCE",
    symbol="BTCUSDT",
    timeframe="1d",
    indicators=["RSI", "Stoch.K", "MACD.macd", "EMA50"]
)
```

!!! note
    Free TradingView accounts are limited to 2 indicators maximum when streaming. Premium accounts can access more indicators simultaneously.

## Supported Languages

The system supports 22 languages for localization and internationalization.

### Language Codes and Names

| Language | Code | Language | Code |
|----------|------|----------|------|
| English | `en` | Swedish | `sv` |
| German | `de` | Turkish | `tr` |
| French | `fr` | Thai | `th` |
| Spanish | `es` | Vietnamese | `vi` |
| Italian | `it` | Indonesian | `id` |
| Portuguese | `pt` | Persian | `fa` |
| Russian | `ru` | Chinese | `ch` |
| Japanese | `ja` | Malay | `ms` |
| Korean | `ko` | Greek | `el` |
| Arabic | `ar` | Hebrew | `he` |
| Hindi | `hi` |  |  |

### Usage Example

```python
# Language support is typically used in UI/localization contexts
# Example: Setting language preference
language_code = "en"  # Use codes from languages.json
```

## Supported News Providers

The system supports 16 news providers for financial and cryptocurrency news.

### News Provider List

| Provider Code | Description |
|---------------|-------------|
| `the_block` | The Block - Crypto news |
| `cointelegraph` | Cointelegraph - Crypto news |
| `beincrypto` | BeInCrypto - Crypto news |
| `newsbtc` | NewsBTC - Crypto news |
| `dow-jones` | Dow Jones - Financial news |
| `cryptonews` | CryptoNews - Crypto news |
| `coindesk` | CoinDesk - Crypto news |
| `cryptoglobe` | CryptoGlobe - Crypto news |
| `tradingview` | TradingView - Market analysis |
| `zycrypto` | ZyCrypto - Crypto news |
| `todayq` | Todayq - Financial news |
| `cryptopotato` | CryptoPotato - Crypto news |
| `u_today` | U.Today - Crypto news |
| `cryptobriefing` | CryptoBriefing - Crypto news |
| `coindar` | Coindar - Crypto events |
| `bitcoin_com` | Bitcoin.com - Crypto news |

### Usage Example

```python
# Filter news by specific provider
news_scraper.scrape_headlines(
    symbol='BTCUSD',
    exchange='BINANCE',
    provider='cointelegraph',  # Must match exactly with news_providers.txt
    sort='latest'
)
```

## Supported Timeframes

The system supports various timeframes for technical analysis and charting.

### Timeframe Codes and Values

| Timeframe | Code Value | Description |
|-----------|------------|-------------|
| `1m` | `"1"` | 1 minute |
| `5m` | `"5"` | 5 minutes |
| `15m` | `"15"` | 15 minutes |
| `30m` | `"30"` | 30 minutes |
| `1h` | `"60"` | 1 hour |
| `2h` | `"120"` | 2 hours |
| `4h` | `"240"` | 4 hours |
| `1d` | `""` | 1 day (empty string) |
| `1w` | `"1W"` | 1 week |
| `1M` | `"1M"` | 1 month |

### Usage Example

```python
# Use different timeframes for analysis
indicators_scraper.scrape(
    exchange="BINANCE",
    symbol="BTCUSDT",
    timeframe="1d",  # Use keys from timeframes.json
    indicators=["RSI", "Stoch.K"]
)

# For streaming with specific timeframe
streamer = Streamer(
    symbol="BTCUSDT",
    indicators=[("STD;RSI", "37.0")],
    timeframe="1m"  # Must match timeframes.json keys
)
```

## Behavioral Notes from Code and Tests

1. **Case Sensitivity**: Exchange names, provider codes, and area codes must match exactly with the values in the data files.

2. **Validation**: The system validates inputs against these supported lists before making API calls.

3. **Error Handling**: Invalid exchanges, providers, or areas will raise appropriate exceptions.

4. **Rate Limits**: Free TradingView accounts have limitations (e.g., 2 indicator maximum for streaming).

5. **Data Consistency**: All modules reference the same data files for consistency.

## Common Mistakes and Solutions

### Mistake: Using unsupported exchange
```python
# Wrong
indicators_scraper.scrape(exchange="INVALID_EXCHANGE", ...)

# Right
indicators_scraper.scrape(exchange="BINANCE", ...)
```

**Solution**: Always check [`tradingview_scraper/data/exchanges.txt`](https://github.com/smitkunpara/tradingview-scraper/blob/main/tradingview_scraper/data/exchanges.txt) for valid exchanges.

### Mistake: Incorrect timeframe format
```python
# Wrong
indicators_scraper.scrape(timeframe="1hour", ...)

# Right
indicators_scraper.scrape(timeframe="1h", ...)
```

**Solution**: Use the exact timeframe keys from [`tradingview_scraper/data/timeframes.json`](https://github.com/smitkunpara/tradingview-scraper/blob/main/tradingview_scraper/data/timeframes.json).

### Mistake: Exceeding indicator limit on free account
```python
# This will fail on free accounts
streamer = Streamer(
    symbol="BTCUSDT",
    indicators=[("STD;RSI", "37.0"), ("STD;MACD", "31.0"), ("STD;CCI", "37.0")],
    timeframe="1m"
)
```

**Solution**: Free accounts can only stream 2 indicators. Upgrade to premium or use fewer indicators.

## Environment Setup

To work with this data, ensure your environment is properly set up:

```bash
# Create and activate virtual environment
uv venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows

# Install dependencies
uv sync
```

This documentation provides the complete reference for all supported data types in the TradingView Scraper system. Always refer to the actual data files for the most up-to-date information.