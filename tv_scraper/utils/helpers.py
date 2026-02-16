"""Helper utilities for tv_scraper."""

import random


def generate_user_agent() -> str:
    """Generate a random Google bot user agent string.

    Returns:
        A random Google bot user agent string.
    """
    user_agents = [
        "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        "Mozilla/5.0 (compatible; Googlebot-Image/1.0; +http://www.google.com/bot.html)",
        "Mozilla/5.0 (compatible; Googlebot-News; +http://www.google.com/bot.html)",
        "Mozilla/5.0 (compatible; Googlebot-Video/1.0; +http://www.google.com/bot.html)",
        "Mozilla/5.0 (compatible; Googlebot-AdsBot/1.0; +http://www.google.com/bot.html)",
        "Mozilla/5.0 (compatible; Google-Site-Verification/1.0; +http://www.google.com/bot.html)",
    ]
    return random.choice(user_agents)


def format_symbol(exchange: str, symbol: str) -> str:
    """Format an exchange and symbol into TradingView's ``EXCHANGE:SYMBOL`` notation.

    Args:
        exchange: Exchange name (e.g. ``"NASDAQ"``).
        symbol: Symbol name (e.g. ``"AAPL"``).

    Returns:
        Formatted string like ``"NASDAQ:AAPL"``.
    """
    return f"{exchange.upper()}:{symbol.upper()}"
