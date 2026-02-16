# GEMINI.md - TV Scraper Project Context

## Project Overview
**TV Scraper** is a powerful Python library designed to extract financial data, technical indicators, and trading ideas from TradingView.com. It supports both HTTP-based scraping (for historical and fundamental data) and WebSocket-based streaming (for real-time OHLCV and indicator updates).

### Main Technologies
- **Python 3.11+**: Core programming language.
- **uv**: Dependency management and project workflow.
- **requests**: Synchronous HTTP requests for scraping.
- **websocket-client**: Low-level WebSocket protocol handling.
- **pandas**: Used for data manipulation and CSV export.
- **pydantic**: Data validation and type enforcement.
- **pytest**: Robust unit and integration testing suite.

### Architecture
The project follows a modular architecture under the `tv_scraper` package:
- `tv_scraper/core/`: Contains base classes (`BaseScraper`), shared constants, exception hierarchy, and the `DataValidator` singleton.
- `tv_scraper/scrapers/`: Individual scraper modules categorized by data type:
    - `market_data/`: Technicals (indicators), Overview, Fundamentals, Markets, Options.
    - `social/`: Ideas, Minds, News.
    - `screening/`: Screener, Market Movers, Symbol Markets.
    - `events/`: Calendar (dividends, earnings).
- `tv_scraper/streaming/`: WebSocket implementations for live data (`Streamer`, `RealTimeData`).
    - `Streamer` includes `get_available_indicators()` to retrieve valid indicator IDs and versions.
    - **Performance optimizations (v1.0.0+)**: TCP_NODELAY socket option, dual session subscriptions (quote + chart), and enhanced message processing for low-latency streaming (~3-4 second update frequency).
- `tv_scraper/utils/`: HTTP wrappers, I/O utilities, and general helpers.
- `tv_scraper/data/`: Static JSON files used by the `DataValidator` for verifying exchanges, indicators, etc.

## Building and Running

### Installation
Use `uv` to sync the environment and install dependencies:
```bash
uv sync
```

### Running Tests
Execute the full test suite using `pytest`:
```bash
uv run pytest tests
```

### Live API Verification
To check if the TradingView endpoints are currently active, run the smoke tests:
```bash
uv run pytest tests/live_api
```

### Manual Testing
Temporary scripts for manual verification with real APIs are located in the `temp/` directory:
- `temp/manual_test.py`: Verifies core features (candles, ideas, minds, news, technicals).
- `temp/manual_test_part2.py`: Verifies remaining features (overview, fundamentals, markets, screener, movers, calendar, real-time).

## Development Conventions

### Coding Style
- **Naming**: Use `snake_case` for all parameters, functions, and variables.
- **Typing**: 100% type hints are required for all public and private methods.
- **Docstrings**: Use Google-style docstrings for all public classes and methods.
- **Imports**: Prefer absolute imports starting from `tv_scraper`.

### Standardized Response Envelope
All public scraper methods return a standardized dictionary:
```python
{
    "status": "success",   # or "failed"
    "data": { ... },       # payload (list, dict, or None on failure)
    "metadata": { ... },   # contextual info (symbol, exchange, etc.)
    "error": None          # error message string, or None on success
}
```

### Error Handling
- Public methods in the `scrapers` and `streaming` modules should **never raise exceptions** for data or network errors. Instead, they catch errors internally and return a "failed" response envelope.
- Validation errors are handled by the `DataValidator` and converted into standardized error responses by the scraper subclasses.

### Data Export
Scrapers support automatic file export via `export_result=True` and `export_type='json'` or `'csv'`. Files are saved to the `export/` directory with timestamped filenames.

## WebSocket Streaming Implementation

### Connection Optimization
The streaming module (`tv_scraper.streaming`) establishes WebSocket connections with performance optimizations:
- **TCP_NODELAY**: Disables Nagle's algorithm for immediate packet transmission, reducing latency
- **Socket Configuration**: Applied via `sockopt` parameter during connection creation

### Message Types
The streaming system processes multiple message types for comprehensive data coverage:
- **QSD (Quote Session Data)**: Quote-level updates with price, volume, bid/ask, and change data
- **DU (Data Update)**: Chart session updates with real-time OHLCV data from 1-second timeframe
- **Heartbeat (~h~)**: Keep-alive messages that are automatically echoed back

### Dual Session Strategy
Real-time price streaming (`stream_realtime_price()`) subscribes to both:
1. **Quote Session**: Provides quote data every few seconds
2. **Chart Session**: Provides 1-second OHLCV updates for faster price changes

This dual approach ensures maximum update frequency (~1 update per 3-4 seconds) matching browser performance.

### Testing
- **Unit Tests**: Mock all WebSocket connections (`tests/unit/test_streaming.py`)
- **Live API Tests**: Verify real-world streaming with actual connections (`tests/live_api/test_streaming.py`)
- **Comprehensive Coverage**: Tests include timeframes, multiple exchanges, error handling, and connection stability
