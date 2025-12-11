# TV Scraper

<div align="center" markdown="1">

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![License](https://img.shields.io/github/license/smitkunpara/tv-scraper.svg)

**The most comprehensive and powerful Python library for programmatic access to TradingView data.**

[Get Started](quick_start.md){ .md-button .md-button--primary } [View on GitHub](https://github.com/smitkunpara/tv-scraper){ .md-button .md-button--secondary }

---

## Attribution

This project is based on [mnwato/tradingview-scraper](https://github.com/mnwato/tradingview-scraper). Thanks to the original author for the foundational work.

</div>

---

## 🚀 Introduction

**TradingView Scraper** is a robust Python library designed to bridge the gap between TradingView's visual data and your algorithmic needs. Whether you are building a trading bot, a market analysis dashboard, or a research tool, this library allows you to extract real-time and historical data directly from TradingView without the need for an official API key.

It goes beyond simple price scraping, offering deep access to:
- **Technical Analysis**: 80+ built-in indicators (RSI, MACD, Bollinger Bands, etc.) calculated in real-time.
- **Social Sentiment**: Community Ideas, Minds discussions, and News sentiment.
- **Fundamental Data**: Financial statements, ratios, and company overview.
- **Live Streaming**: WebSocket integration for real-time OHLCV and indicator updates.

## ⚡ Quick Glance

Get up and running in seconds. Here's how to fetch technical indicators for Bitcoin:

```python
from tradingview_scraper.symbols.technicals import Indicators

# Initialize the scraper
scraper = Indicators()

# Get RSI and MACD for BTCUSD on Binance
data = scraper.scrape(
    exchange="BINANCE",
    symbol="BTCUSD",
    timeframe="1d",
    indicators=["RSI", "MACD"]
)

print(data)
```

## 📦 Key Modules

The library is organized into specialized modules to handle different types of data efficiently:

| Module | Description |
| :--- | :--- |
| **[`Indicators`](indicators.md)** | Fetch values for standard and custom technical indicators. |
| **[`Streamer`](realtime.md)** | Connect to WebSocket for live price and indicator updates. |
| **[`Ideas`](ideas.md)** | Scrape trading ideas, strategies, and educational content. |
| **[`News`](news.md)** | Access real-time news headlines and detailed articles. |
| **[`Screener`](screener.md)** | Filter stocks, crypto, and forex based on technical/fundamental criteria. |
| **[`Fundamentals`](fundamentals.md)** | Retrieve balance sheets, income statements, and cash flow. |
| **[`MarketMovers`](market_movers.md)** | Identify top gainers, losers, and active symbols. |

## ✨ Why TradingView Scraper?

- **Zero Configuration**: No API keys required for most features. Works out of the box.
- **Broad Coverage**: Supports **260+ exchanges** (Binance, NASDAQ, NYSE, Forex) and **18+ markets**.
- **Real-Time & Historical**: switch seamlessly between scraping static data and streaming live updates.
- **Developer Friendly**: Fully typed, structured JSON output, and built with modern Python (3.11+).
- **Export Ready**: Built-in support for exporting data to **JSON** and **CSV** for analysis.


## 📚 Next Steps

- Follow the [**Quick Start Guide**](quick_start.md) to set up your first scraper.
- Explore [**Supported Data**](supported_data.md) to see available exchanges and indicators.
- Learn about [**Real-time Streaming**](realtime.md) for live data applications.

---
<p align="center">
    <em>Built with ❤️ for the algorithmic trading community.</em>
</p>
