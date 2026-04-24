# Getting Cookies

Use a TradingView session cookie when a scraper hits a captcha challenge or when a feature requires authenticated access.

## When You Need A Cookie

- `Pine` always requires one
- `Ideas` may need one after TradingView presents a captcha
- `CandleStreamer` may need one for custom or private indicators
- any workflow where you want the library to reuse your authenticated TradingView session

## How To Capture The Cookie

1. Open a TradingView page in your browser, for example `https://www.tradingview.com/symbols/BTCUSD/ideas/`.
2. Open developer tools and switch to the **Network** tab.
3. If a captcha appears, solve it.
4. Refresh the page once the captcha is complete.
5. Open the page request in the Network list.
6. Copy the full `Cookie` request header value.

## Use It In Code

### Ideas

```python
from tv_scraper import Ideas

TRADINGVIEW_COOKIE = "paste_your_cookie_here"

scraper = Ideas(cookie=TRADINGVIEW_COOKIE)
result = scraper.get_ideas(
    exchange="CRYPTO",
    symbol="BTCUSD",
    start_page=1,
    end_page=2,
)
```

### Pine

```python
from tv_scraper import Pine

pine = Pine(cookie=TRADINGVIEW_COOKIE)
result = pine.list_saved_scripts()
```

### CandleStreamer With Indicators

```python
from tv_scraper import CandleStreamer

streamer = CandleStreamer(cookie=TRADINGVIEW_COOKIE)
result = streamer.get_candles(
    exchange="BINANCE",
    symbol="BTCUSDT",
    indicators=[("STD;RSI", "37.0")],
)
```

## Environment Variable Option

If you do not want to pass the cookie to every constructor, set:

```bash
export TRADINGVIEW_COOKIE='paste_your_cookie_here'
```

Then create scrapers normally:

```python
from tv_scraper import Pine

pine = Pine()
```

## Expiration

Cookies are not permanent. If a request starts failing with captcha or auth-related errors again, capture a fresh cookie and retry.
