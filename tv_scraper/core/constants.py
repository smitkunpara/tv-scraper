"""Constants for tv_scraper."""

BASE_URL: str = "https://www.tradingview.com"
SCANNER_URL: str = "https://scanner.tradingview.com"
WEBSOCKET_URL: str = "wss://data.tradingview.com/socket.io/websocket"
REQUEST_TIMEOUT: int = 10
DEFAULT_LIMIT: int = 50
STATUS_SUCCESS: str = "success"
STATUS_FAILED: str = "failed"
EXPORT_TYPES: set[str] = {"json", "csv"}
CAPTCHA_MARKER: str = "<title>Captcha Challenge</title>"

DEFAULT_USER_AGENT: str = (
    "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
)

CHART_SESSION_URL: str = "https://www.tradingview.com/chart/?symbol=BINANCE%3ABTCUSD"
