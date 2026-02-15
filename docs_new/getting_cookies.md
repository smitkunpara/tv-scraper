# Getting Cookies

TradingView may present captcha challenges when scraping ideas to prevent automated access. To continue scraping without interruptions, you need to obtain and use a valid session cookie after manually solving the captcha.

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

Once you have the cookie string, you can use it directly in Python 

```python
from tradingview_scraper.symbols.ideas import Ideas

# Your copied cookie string
TRADINGVIEW_COOKIE = r"paste_your_cookie_string_here"

# Initialize scraper with cookie
ideas_scraper = Ideas(cookie=TRADINGVIEW_COOKIE)

# Scrape ideas
ideas = ideas_scraper.scrape(symbol="BTCUSD", startPage=1, endPage=5)
```

!!! warning "Cookie Expiration"
    The cookie remains valid for approximately 24 hours. After that, you'll need to repeat the process to get a new cookie when scraping encounters captcha challenges again.