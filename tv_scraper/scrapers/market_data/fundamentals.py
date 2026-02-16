"""Fundamentals scraper for fetching financial data from TradingView."""

import logging
from typing import Any, Dict, List, Optional

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.constants import SCANNER_URL
from tv_scraper.core.exceptions import NetworkError, ValidationError

logger = logging.getLogger(__name__)


class Fundamentals(BaseScraper):
    """Scraper for fundamental financial data from TradingView.

    Fetches income statement, balance sheet, cash flow, margins, profitability,
    liquidity, leverage, valuation, and dividend data via the TradingView
    scanner API.

    Args:
        export_result: Whether to export results to file.
        export_type: Export format, ``"json"`` or ``"csv"``.
        timeout: HTTP request timeout in seconds.

    Example::

        from tv_scraper.scrapers.market_data import Fundamentals

        scraper = Fundamentals()
        data = scraper.get_fundamentals(exchange="NASDAQ", symbol="AAPL")
    """

    INCOME_STATEMENT_FIELDS: List[str] = [
        "total_revenue",
        "revenue_per_share_ttm",
        "total_revenue_fy",
        "gross_profit",
        "gross_profit_fy",
        "operating_income",
        "operating_income_fy",
        "net_income",
        "net_income_fy",
        "EBITDA",
        "basic_eps_net_income",
        "earnings_per_share_basic_ttm",
        "earnings_per_share_diluted_ttm",
    ]

    BALANCE_SHEET_FIELDS: List[str] = [
        "total_assets",
        "total_assets_fy",
        "cash_n_short_term_invest",
        "cash_n_short_term_invest_fy",
        "total_debt",
        "total_debt_fy",
        "stockholders_equity",
        "stockholders_equity_fy",
        "book_value_per_share_fq",
    ]

    CASH_FLOW_FIELDS: List[str] = [
        "cash_f_operating_activities",
        "cash_f_operating_activities_fy",
        "cash_f_investing_activities",
        "cash_f_investing_activities_fy",
        "cash_f_financing_activities",
        "cash_f_financing_activities_fy",
        "free_cash_flow",
    ]

    MARGIN_FIELDS: List[str] = [
        "gross_margin",
        "gross_margin_percent_ttm",
        "operating_margin",
        "operating_margin_ttm",
        "pretax_margin_percent_ttm",
        "net_margin",
        "net_margin_percent_ttm",
        "EBITDA_margin",
    ]

    PROFITABILITY_FIELDS: List[str] = [
        "return_on_equity",
        "return_on_equity_fq",
        "return_on_assets",
        "return_on_assets_fq",
        "return_on_investment_ttm",
    ]

    LIQUIDITY_FIELDS: List[str] = [
        "current_ratio",
        "current_ratio_fq",
        "quick_ratio",
        "quick_ratio_fq",
    ]

    LEVERAGE_FIELDS: List[str] = [
        "debt_to_equity",
        "debt_to_equity_fq",
        "debt_to_assets",
    ]

    VALUATION_FIELDS: List[str] = [
        "market_cap_basic",
        "market_cap_calc",
        "market_cap_diluted_calc",
        "enterprise_value_fq",
        "price_earnings_ttm",
        "price_book_fq",
        "price_sales_ttm",
        "price_free_cash_flow_ttm",
    ]

    DIVIDEND_FIELDS: List[str] = [
        "dividends_yield",
        "dividends_per_share_fq",
        "dividend_payout_ratio_ttm",
    ]

    ALL_FIELDS: List[str] = (
        INCOME_STATEMENT_FIELDS
        + BALANCE_SHEET_FIELDS
        + CASH_FLOW_FIELDS
        + MARGIN_FIELDS
        + PROFITABILITY_FIELDS
        + LIQUIDITY_FIELDS
        + LEVERAGE_FIELDS
        + VALUATION_FIELDS
        + DIVIDEND_FIELDS
    )

    # Default fields used for multi-symbol comparison when none specified
    DEFAULT_COMPARISON_FIELDS: List[str] = [
        "total_revenue",
        "net_income",
        "EBITDA",
        "market_cap_basic",
        "price_earnings_ttm",
        "return_on_equity_fq",
        "debt_to_equity_fq",
    ]

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

    def get_fundamentals(
        self,
        exchange: str,
        symbol: str,
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get fundamental financial data for a symbol.

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
                data_category="fundamentals",
            )

        return self._success_response(
            result,
            exchange=exchange,
            symbol=symbol,
        )

    def compare_fundamentals(
        self,
        symbols: List[Dict[str, str]],
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Compare fundamental data across multiple symbols.

        Args:
            symbols: List of dicts with ``"exchange"`` and ``"symbol"`` keys.
            fields: Specific fields to compare. If ``None``, uses
                ``DEFAULT_COMPARISON_FIELDS``.

        Returns:
            Standardized response dict. On success, ``data`` contains
            ``items`` (list of per-symbol dicts) and ``comparison`` (field →
            symbol → value mapping).
        """
        if not symbols:
            return self._error_response("No symbols provided for comparison.")

        field_list = fields if fields else self.DEFAULT_COMPARISON_FIELDS

        all_items: List[Dict[str, Any]] = []
        comparison: Dict[str, Dict[str, Any]] = {}

        for sym in symbols:
            exchange = sym.get("exchange", "")
            symbol_name = sym.get("symbol", "")
            result = self.get_fundamentals(
                exchange=exchange, symbol=symbol_name, fields=field_list
            )
            if result["status"] != "success":
                continue

            item_data = result["data"]
            all_items.append(item_data)

            combined = f"{exchange}:{symbol_name}"
            for field in field_list:
                if field not in comparison:
                    comparison[field] = {}
                comparison[field][combined] = item_data.get(field)

        if not all_items:
            return self._error_response("No data retrieved for any symbols.")

        data: Dict[str, Any] = {
            "items": all_items,
            "comparison": comparison,
        }

        # --- Export ---
        if self.export_result:
            self._export(
                data=data,
                symbol="comparison",
                data_category="fundamentals",
            )

        return self._success_response(data)

    # ---- Category helpers ------------------------------------------------

    def get_income_statement(
        self, exchange: str, symbol: str
    ) -> Dict[str, Any]:
        """Get income statement data for a symbol.

        Args:
            exchange: Exchange name (e.g. ``"NASDAQ"``).
            symbol: Trading symbol (e.g. ``"AAPL"``).

        Returns:
            Income statement data including revenue, profit, earnings.
        """
        return self.get_fundamentals(
            exchange=exchange, symbol=symbol, fields=self.INCOME_STATEMENT_FIELDS
        )

    def get_balance_sheet(
        self, exchange: str, symbol: str
    ) -> Dict[str, Any]:
        """Get balance sheet data for a symbol.

        Args:
            exchange: Exchange name (e.g. ``"NASDAQ"``).
            symbol: Trading symbol (e.g. ``"AAPL"``).

        Returns:
            Balance sheet data including assets, debt, equity.
        """
        return self.get_fundamentals(
            exchange=exchange, symbol=symbol, fields=self.BALANCE_SHEET_FIELDS
        )

    def get_cash_flow(
        self, exchange: str, symbol: str
    ) -> Dict[str, Any]:
        """Get cash flow statement data for a symbol.

        Args:
            exchange: Exchange name (e.g. ``"NASDAQ"``).
            symbol: Trading symbol (e.g. ``"AAPL"``).

        Returns:
            Cash flow data including operating, investing, financing activities.
        """
        return self.get_fundamentals(
            exchange=exchange, symbol=symbol, fields=self.CASH_FLOW_FIELDS
        )

    def get_statistics(
        self, exchange: str, symbol: str
    ) -> Dict[str, Any]:
        """Get statistics data for a symbol.

        Combines liquidity, leverage, and valuation fields.

        Args:
            exchange: Exchange name (e.g. ``"NASDAQ"``).
            symbol: Trading symbol (e.g. ``"AAPL"``).

        Returns:
            Statistics data including ratios and valuation metrics.
        """
        fields = self.LIQUIDITY_FIELDS + self.LEVERAGE_FIELDS + self.VALUATION_FIELDS
        return self.get_fundamentals(
            exchange=exchange, symbol=symbol, fields=fields
        )

    def get_dividends(
        self, exchange: str, symbol: str
    ) -> Dict[str, Any]:
        """Get dividend information for a symbol.

        Args:
            exchange: Exchange name (e.g. ``"NASDAQ"``).
            symbol: Trading symbol (e.g. ``"AAPL"``).

        Returns:
            Dividend data including yield, per share, payout ratio.
        """
        return self.get_fundamentals(
            exchange=exchange, symbol=symbol, fields=self.DIVIDEND_FIELDS
        )

    def get_profitability(
        self, exchange: str, symbol: str
    ) -> Dict[str, Any]:
        """Get profitability ratios for a symbol.

        Args:
            exchange: Exchange name (e.g. ``"NASDAQ"``).
            symbol: Trading symbol (e.g. ``"AAPL"``).

        Returns:
            Profitability data including ROE, ROA, ROI.
        """
        return self.get_fundamentals(
            exchange=exchange, symbol=symbol, fields=self.PROFITABILITY_FIELDS
        )

    def get_margins(
        self, exchange: str, symbol: str
    ) -> Dict[str, Any]:
        """Get margin metrics for a symbol.

        Args:
            exchange: Exchange name (e.g. ``"NASDAQ"``).
            symbol: Trading symbol (e.g. ``"AAPL"``).

        Returns:
            Margin data including gross, operating, net, EBITDA margins.
        """
        return self.get_fundamentals(
            exchange=exchange, symbol=symbol, fields=self.MARGIN_FIELDS
        )
