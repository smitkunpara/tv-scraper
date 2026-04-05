"""Overview scraper for fetching comprehensive symbol data from TradingView."""

from typing import Any

from tv_scraper.core.base import BaseScraper


class Overview(BaseScraper):
    """Scraper for comprehensive symbol overview data from TradingView.

    Fetches profile, statistics, financials, performance, and technical
    data for a given symbol via the TradingView scanner API.

    Args:
        export_result: Whether to export results to file.
        export_type: Export format, ``"json"`` or ``"csv"``.
        timeout: HTTP request timeout in seconds.

    Example::

        from tv_scraper.scrapers.market_data import Overview

        scraper = Overview()
        data = scraper.get_overview(exchange="NASDAQ", symbol="AAPL")
    """

    BASIC_FIELDS: list[str] = [
        "name",
        "description",
        "type",
        "subtype",
        "exchange",
        "country",
        "sector",
        "industry",
    ]

    PRICE_FIELDS: list[str] = [
        "close",
        "change",
        "change_abs",
        "change_from_open",
        "high",
        "low",
        "open",
        "volume",
        "Value.Traded",
        "price_52_week_high",
        "price_52_week_low",
    ]

    MARKET_FIELDS: list[str] = [
        "market_cap_basic",
        "market_cap_calc",
        "market_cap_diluted_calc",
        "shares_outstanding",
        "shares_float",
        "shares_diluted",
    ]

    VALUATION_FIELDS: list[str] = [
        "price_earnings_ttm",
        "price_book_fq",
        "price_sales_ttm",
        "price_free_cash_flow_ttm",
        "earnings_per_share_basic_ttm",
        "earnings_per_share_diluted_ttm",
        "book_value_per_share_fq",
    ]

    DIVIDEND_FIELDS: list[str] = [
        "dividends_yield",
        "dividends_per_share_fq",
        "dividend_payout_ratio_ttm",
    ]

    FINANCIAL_FIELDS: list[str] = [
        "total_revenue",
        "revenue_per_share_ttm",
        "net_income_fy",
        "gross_margin_percent_ttm",
        "operating_margin_ttm",
        "net_margin_percent_ttm",
        "return_on_equity_fq",
        "return_on_assets_fq",
        "return_on_investment_ttm",
        "debt_to_equity_fq",
        "current_ratio_fq",
        "quick_ratio_fq",
        "EBITDA",
        "employees",
    ]

    PERFORMANCE_FIELDS: list[str] = [
        "Perf.W",
        "Perf.1M",
        "Perf.3M",
        "Perf.6M",
        "Perf.Y",
        "Perf.YTD",
    ]

    VOLATILITY_FIELDS: list[str] = [
        "Volatility.D",
        "Volatility.W",
        "Volatility.M",
        "beta_1_year",
    ]

    TECHNICAL_FIELDS: list[str] = [
        "Recommend.All",
        "RSI",
        "CCI20",
        "ADX",
        "MACD.macd",
        "Stoch.K",
        "ATR",
    ]

    ALL_FIELDS: list[str] = [
        *BASIC_FIELDS,
        *PRICE_FIELDS,
        *MARKET_FIELDS,
        *VALUATION_FIELDS,
        *DIVIDEND_FIELDS,
        *FINANCIAL_FIELDS,
        *PERFORMANCE_FIELDS,
        *VOLATILITY_FIELDS,
        *TECHNICAL_FIELDS,
    ]

    def get_overview(
        self,
        exchange: str,
        symbol: str,
        fields: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get comprehensive overview data for a symbol.

        Args:
            exchange: Exchange name (e.g. ``"NASDAQ"``).
            symbol: Trading symbol (e.g. ``"AAPL"``).
            fields: Specific fields to retrieve. If ``None``, retrieves all
                fields defined in ``ALL_FIELDS``.

        Returns:
            Standardized response dict with keys
            ``status``, ``data``, ``metadata``, ``error``.
        """
        if fields is not None and len(fields) == 0:
            return self._error_response(
                "Fields list cannot be empty.",
                exchange=exchange,
                symbol=symbol,
            )
        field_list = fields if fields else self.ALL_FIELDS
        return self._fetch_symbol_fields(
            exchange=exchange,
            symbol=symbol,
            fields=field_list,
            data_category="overview",
        )

    def get_profile(self, exchange: str, symbol: str) -> dict[str, Any]:
        """Get basic profile information for a symbol.

        Args:
            exchange: Exchange name (e.g. ``"NASDAQ"``).
            symbol: Trading symbol (e.g. ``"AAPL"``).

        Returns:
            Profile data including name, description, exchange, sector, industry.
        """
        return self.get_overview(
            exchange=exchange, symbol=symbol, fields=self.BASIC_FIELDS
        )

    def get_statistics(self, exchange: str, symbol: str) -> dict[str, Any]:
        """Get market statistics for a symbol.

        Args:
            exchange: Exchange name (e.g. ``"NASDAQ"``).
            symbol: Trading symbol (e.g. ``"AAPL"``).

        Returns:
            Statistics including market cap, shares, valuation ratios.
        """
        fields = self.MARKET_FIELDS + self.VALUATION_FIELDS + self.DIVIDEND_FIELDS
        return self.get_overview(exchange=exchange, symbol=symbol, fields=fields)

    def get_financials(self, exchange: str, symbol: str) -> dict[str, Any]:
        """Get financial metrics for a symbol.

        Args:
            exchange: Exchange name (e.g. ``"NASDAQ"``).
            symbol: Trading symbol (e.g. ``"AAPL"``).

        Returns:
            Financial data including revenue, margins, ratios, EBITDA.
        """
        return self.get_overview(
            exchange=exchange, symbol=symbol, fields=self.FINANCIAL_FIELDS
        )

    def get_performance(self, exchange: str, symbol: str) -> dict[str, Any]:
        """Get performance metrics for a symbol.

        Args:
            exchange: Exchange name (e.g. ``"NASDAQ"``).
            symbol: Trading symbol (e.g. ``"AAPL"``).

        Returns:
            Performance data including weekly, monthly, yearly returns.
        """
        return self.get_overview(
            exchange=exchange, symbol=symbol, fields=self.PERFORMANCE_FIELDS
        )

    def get_technicals(self, exchange: str, symbol: str) -> dict[str, Any]:
        """Get technical indicators for a symbol.

        Args:
            exchange: Exchange name (e.g. ``"NASDAQ"``).
            symbol: Trading symbol (e.g. ``"AAPL"``).

        Returns:
            Technical indicators including RSI, MACD, ADX, recommendations.
        """
        fields = self.TECHNICAL_FIELDS + self.VOLATILITY_FIELDS
        return self.get_overview(exchange=exchange, symbol=symbol, fields=fields)
