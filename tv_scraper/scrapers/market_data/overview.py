"""Overview scraper for fetching comprehensive symbol data from TradingView."""

import logging
from typing import Any, Dict, List, Optional

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.constants import SCANNER_URL
from tv_scraper.core.exceptions import NetworkError, ValidationError

logger = logging.getLogger(__name__)


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

    BASIC_FIELDS: List[str] = [
        "name",
        "description",
        "type",
        "subtype",
        "exchange",
        "country",
        "sector",
        "industry",
    ]

    PRICE_FIELDS: List[str] = [
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

    MARKET_FIELDS: List[str] = [
        "market_cap_basic",
        "market_cap_calc",
        "market_cap_diluted_calc",
        "shares_outstanding",
        "shares_float",
        "shares_diluted",
    ]

    VALUATION_FIELDS: List[str] = [
        "price_earnings_ttm",
        "price_book_fq",
        "price_sales_ttm",
        "price_free_cash_flow_ttm",
        "earnings_per_share_basic_ttm",
        "earnings_per_share_diluted_ttm",
        "book_value_per_share_fq",
    ]

    DIVIDEND_FIELDS: List[str] = [
        "dividends_yield",
        "dividends_per_share_fq",
        "dividend_payout_ratio_ttm",
    ]

    FINANCIAL_FIELDS: List[str] = [
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

    PERFORMANCE_FIELDS: List[str] = [
        "Perf.W",
        "Perf.1M",
        "Perf.3M",
        "Perf.6M",
        "Perf.Y",
        "Perf.YTD",
    ]

    VOLATILITY_FIELDS: List[str] = [
        "Volatility.D",
        "Volatility.W",
        "Volatility.M",
        "beta_1_year",
    ]

    TECHNICAL_FIELDS: List[str] = [
        "Recommend.All",
        "RSI",
        "CCI20",
        "ADX",
        "MACD.macd",
        "Stoch.K",
        "ATR",
    ]

    ALL_FIELDS: List[str] = (
        BASIC_FIELDS
        + PRICE_FIELDS
        + MARKET_FIELDS
        + VALUATION_FIELDS
        + DIVIDEND_FIELDS
        + FINANCIAL_FIELDS
        + PERFORMANCE_FIELDS
        + VOLATILITY_FIELDS
        + TECHNICAL_FIELDS
    )

    def __init__(
        self,
        export_result: bool = False,
        export_type: str = "json",
        timeout: int = 10,
    ) -> None:
        super().__init__(
            export_result=export_result,
            export_type=export_type,
            timeout=timeout,
        )

    def get_overview(
        self,
        exchange: str,
        symbol: str,
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get comprehensive overview data for a symbol.

        Args:
            exchange: Exchange name (e.g. ``"NASDAQ"``). Can be empty if
                combined symbol is used in the `symbol` parameter.
            symbol: Trading symbol (e.g. ``"AAPL"``) or combined
                ``"EXCHANGE:SYMBOL"`` string (e.g. ``"NASDAQ:AAPL"``).
            fields: Specific fields to retrieve. If ``None``, retrieves all
                fields defined in ``ALL_FIELDS``.

        Returns:
            Standardized response dict with keys
            ``status``, ``data``, ``metadata``, ``error``.
        """
        # Support combined EXCHANGE:SYMBOL
        if not exchange and ":" in symbol:
            exchange, symbol = symbol.split(":", 1)

        # --- Validation ---
        try:
            self.validator.validate_exchange(exchange)
            self.validator.validate_symbol(exchange, symbol)
        except ValidationError as exc:
            return self._error_response(str(exc))

        # Determine fields to request
        field_list = fields if fields else self.ALL_FIELDS

        # --- Build API request ---
        url = f"{SCANNER_URL}/symbol"
        params: Dict[str, str] = {
            "symbol": f"{exchange}:{symbol}",
            "fields": ",".join(field_list),
            "no_404": "true",
        }

        # --- Execute request ---
        try:
            response = self._make_request(url, method="GET", params=params)
            json_response: Dict[str, Any] = response.json()
        except NetworkError as exc:
            return self._error_response(str(exc))
        except (ValueError, KeyError) as exc:
            return self._error_response(f"Failed to parse API response: {exc}")

        # --- Parse response ---
        if not json_response:
            return self._error_response("No data returned from API.")

        # API returns a flat dict of field:value
        result: Dict[str, Any] = {"symbol": f"{exchange}:{symbol}"}
        for field in field_list:
            result[field] = json_response.get(field)

        # --- Export ---
        if self.export_result:
            self._export(
                data=result,
                symbol=f"{exchange}_{symbol}",
                data_category="overview",
            )

        return self._success_response(
            result,
            exchange=exchange,
            symbol=symbol,
        )

    def get_profile(self, exchange: str, symbol: str) -> Dict[str, Any]:
        """Get basic profile information for a symbol.

        Args:
            exchange: Exchange name (e.g. ``"NASDAQ"``).
            symbol: Trading symbol (e.g. ``"AAPL"``).

        Returns:
            Profile data including name, description, exchange, sector, industry.
        """
        return self.get_overview(exchange=exchange, symbol=symbol, fields=self.BASIC_FIELDS)

    def get_statistics(self, exchange: str, symbol: str) -> Dict[str, Any]:
        """Get market statistics for a symbol.

        Args:
            exchange: Exchange name (e.g. ``"NASDAQ"``).
            symbol: Trading symbol (e.g. ``"AAPL"``).

        Returns:
            Statistics including market cap, shares, valuation ratios.
        """
        fields = self.MARKET_FIELDS + self.VALUATION_FIELDS + self.DIVIDEND_FIELDS
        return self.get_overview(exchange=exchange, symbol=symbol, fields=fields)

    def get_financials(self, exchange: str, symbol: str) -> Dict[str, Any]:
        """Get financial metrics for a symbol.

        Args:
            exchange: Exchange name (e.g. ``"NASDAQ"``).
            symbol: Trading symbol (e.g. ``"AAPL"``).

        Returns:
            Financial data including revenue, margins, ratios, EBITDA.
        """
        return self.get_overview(exchange=exchange, symbol=symbol, fields=self.FINANCIAL_FIELDS)

    def get_performance(self, exchange: str, symbol: str) -> Dict[str, Any]:
        """Get performance metrics for a symbol.

        Args:
            exchange: Exchange name (e.g. ``"NASDAQ"``).
            symbol: Trading symbol (e.g. ``"AAPL"``).

        Returns:
            Performance data including weekly, monthly, yearly returns.
        """
        return self.get_overview(exchange=exchange, symbol=symbol, fields=self.PERFORMANCE_FIELDS)

    def get_technicals(self, exchange: str, symbol: str) -> Dict[str, Any]:
        """Get technical indicators for a symbol.

        Args:
            exchange: Exchange name (e.g. ``"NASDAQ"``).
            symbol: Trading symbol (e.g. ``"AAPL"``).

        Returns:
            Technical indicators including RSI, MACD, ADX, recommendations.
        """
        fields = self.TECHNICAL_FIELDS + self.VOLATILITY_FIELDS
        return self.get_overview(exchange=exchange, symbol=symbol, fields=fields)
