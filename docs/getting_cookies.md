# Getting Cookies

TradingView may present captcha challenges when scraping ideas or requiring authentication for WebSocket-based indicators in the `Streamer` class. To continue scraping without interruptions and access protected indicators, you need to obtain and use a valid session cookie.

!!! note "Captcha Frequency"
    TradingView typically requires captcha verification every 24 hours. When you encounter a captcha error, you'll need to repeat this process to get a fresh cookie.

## Steps to Obtain Session Cookie

Follow these steps to get a valid TradingView session cookie after solving the captcha:

1. **Open the Ideas Page**: Navigate to `https://www.tradingview.com/symbols/BTCUSD/ideas/` in your web browser.

2. **Open Developer Tools**: Press `F12` to open the browser's developer tools and switch to the **Network** tab.

3. **Solve the Captcha**: If a captcha challenge appears, complete it manually.

4. **Refresh the Page**: After solving the captcha, refresh the page to ensure a clean request.

5. **Capture the Request**: In the Network tab, look for the GET request to `https://www.tradingview.com/symbols/BTCUSD/ideas/` (usually at the top of the list).

6. **Extract the Cookie**:
    - Select the request
    - Go to the **Headers** section
    - Find the **Cookie** header in the request headers
    - Copy the entire cookie value

## Using the Cookie in Code

### With Ideas Scraper

```python
from tv_scraper import Ideas

# Your copied cookie string
TRADINGVIEW_COOKIE = r"paste_your_cookie_string_here"

# Initialize scraper with cookie
ideas_scraper = Ideas(cookie=TRADINGVIEW_COOKIE)

# Scrape ideas
ideas = ideas_scraper.get_ideas(symbol="BTCUSD", exchange="CRYPTO", start_page=1, end_page=5)
```

### With Streamer (for Indicators)

```python
from tv_scraper import Streamer

# Initialize streamer with cookie
s = Streamer(cookie=TRADINGVIEW_COOKIE)

# Get candles with indicators (requires auth)
result = s.get_candles(
    exchange="BINANCE",
    symbol="BTCUSDT",
    indicators=[("STD;RSI", "37.0")]
)
```

!!! warning "Cookie Expiration"
    The cookie remains valid for approximately 24 hours. After that, you'll need to repeat the process to get a new cookie when scraping encounters captcha challenges or indicator authentication fails.
