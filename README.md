# TV Scraper

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MIT License](https://img.shields.io/github/license/smitkunpara/tv-scraper.svg?color=brightgreen)](https://opensource.org/licenses/MIT)

**A high-performance Python library for extracting real-time financial data, technical indicators, and social insights from TradingView.**

---

## ✨ Features

### 📡 Real-Time Streaming
- **🕯️ Candle + Indicators**: Stream live OHLCV candles with built-in or custom Pine indicators via [`CandleStreamer`](https://smitkunpara.github.io/tv-scraper/streaming/candle_streamer/).
- **⚡ Real-time Pricing**: Persistent WebSocket connection for millisecond-accurate price updates.
- **📊 Analyst Forecasts**: Capture analyst price targets, EPS, and revenue estimates for stocks via [`ForecastStreamer`](https://smitkunpara.github.io/tv-scraper/streaming/forecast_streamer/).

### 📉 Financial & Technical Data
- **🧩 Technical Analysis**: Access RSI, MACD, EMAs, and 100+ other indicators via [`Technicals`](https://smitkunpara.github.io/tv-scraper/scrapers/technicals/).
- **🏛️ Fundamentals**: Comprehensive financial statements, ratios, and balance sheets via [`Fundamentals`](https://smitkunpara.github.io/tv-scraper/scrapers/fundamentals/).
- **⛓️ Options Data**: Retrieve full option chains, Greeks, IV, and theoretical prices via [`Options`](https://smitkunpara.github.io/tv-scraper/scrapers/options/).
- **📅 Events Calendar**: Track Earnings, Dividends, IPOs, and Economic events via [`Calendar`](https://smitkunpara.github.io/tv-scraper/scrapers/calendar/).

### 🔍 Discovery & Screening
- **🔎 Screener**: Run advanced market scans with custom filters across 50+ countries via [`Screener`](https://smitkunpara.github.io/tv-scraper/scrapers/screener/).
- **🏁 Market Movers**: Track top gainers, losers, and most active stocks via [`Market Movers`](https://smitkunpara.github.io/tv-scraper/scrapers/market_movers/).
- **🌍 Global Markets**: Discover symbols across exchanges and asset classes via [`Markets`](https://smitkunpara.github.io/tv-scraper/scrapers/markets/).

### 🤝 Social & Community
- **💡 Trading Ideas**: Scrape community-driven trading setups and technical ideas via [`Ideas`](https://smitkunpara.github.io/tv-scraper/scrapers/ideas/).
- **🧠 Heads-up (Minds)**: Access real-time discussions and community posts via [`Minds`](https://smitkunpara.github.io/tv-scraper/scrapers/minds/).
- **📰 News Feed**: Integrated news stream with granular filters by symbol or region via [`News`](https://smitkunpara.github.io/tv-scraper/scrapers/news/).

---

## 🚀 Quick Start

```python
from tv_scraper import CandleStreamer

# Initialize the streamer
streamer = CandleStreamer()

# Fetch real-time candles and indicators
result = streamer.get_candles(
    exchange="BINANCE",
    symbol="BTCUSDT",
    timeframe="1m",
    numb_candles=5,
    indicators=[("STD;RSI", "1.0")]
)

if result["status"] == "success":
    print(result["data"]["ohlcv"])
```

---

## 📚 Documentation

For complete documentation, installation guides, and API references, visit:

**[📖 Full Documentation](https://smitkunpara.github.io/tv-scraper/)**

### Key Resource Links
- [🚀 Quick Start Guide](https://smitkunpara.github.io/tv-scraper/getting-started/)
- [📦 Installation](https://smitkunpara.github.io/tv-scraper/getting-started/#install)
- [📊 Supported Exchanges & Metrics](https://smitkunpara.github.io/tv-scraper/supported_data/)
- [📋 API Conventions](https://smitkunpara.github.io/tv-scraper/api-conventions/)

---

## 🛠️ Development & Contributing

We welcome contributions! Please see our [Contributing Guide](https://smitkunpara.github.io/tv-scraper/contributing/) for details.

- **🐛 Bug Reports**: [Open an issue](https://github.com/smitkunpara/tv-scraper/issues)
- **💡 Feature Requests**: [Start a discussion](https://github.com/smitkunpara/tv-scraper/discussions)

---

## 📄 License

Licensed under the **MIT License**.
