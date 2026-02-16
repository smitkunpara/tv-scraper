"""tv_scraper - A Python library for scraping TradingView data."""

__version__ = "1.0.0"

# Market Data
from tv_scraper.scrapers.market_data.technicals import Technicals
from tv_scraper.scrapers.market_data.overview import Overview
from tv_scraper.scrapers.market_data.fundamentals import Fundamentals
from tv_scraper.scrapers.market_data.markets import Markets
from tv_scraper.scrapers.market_data.options import Options

# Social
from tv_scraper.scrapers.social.ideas import Ideas
from tv_scraper.scrapers.social.minds import Minds
from tv_scraper.scrapers.social.news import News

# Screening
from tv_scraper.scrapers.screening.screener import Screener
from tv_scraper.scrapers.screening.market_movers import MarketMovers
from tv_scraper.scrapers.screening.symbol_markets import SymbolMarkets

# Events
from tv_scraper.scrapers.events.calendar import Calendar

# Streaming
from tv_scraper.streaming.streamer import Streamer
from tv_scraper.streaming.price import RealTimeData

__all__ = [
    "Technicals", "Overview", "Fundamentals", "Markets", "Options",
    "Ideas", "Minds", "News",
    "Screener", "MarketMovers", "SymbolMarkets",
    "Calendar",
    "Streamer", "RealTimeData",
]
