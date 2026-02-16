"""Constants for tv_scraper."""

BASE_URL: str = "https://www.tradingview.com"
SCANNER_URL: str = "https://scanner.tradingview.com"
WEBSOCKET_URL: str = "wss://data.tradingview.com/socket.io/websocket"
DEFAULT_TIMEOUT: int = 10
DEFAULT_LIMIT: int = 50
STATUS_SUCCESS: str = "success"
STATUS_FAILED: str = "failed"
EXPORT_TYPES: set[str] = {"json", "csv"}

# Default scanner fields shared across modules
DEFAULT_SCANNER_FIELDS: list[str] = [
    "name",
    "close",
    "change",
    "change_abs",
    "volume",
    "market_cap_basic",
    "price_earnings_ttm",
    "earnings_per_share_basic_ttm",
]
