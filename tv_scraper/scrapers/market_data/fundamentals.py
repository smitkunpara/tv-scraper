"""Fundamentals scraper for fetching financial data from TradingView."""

from typing import Any

from tv_scraper.core.base import BaseScraper


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

    INCOME_STATEMENT_FIELDS: list[str] = [
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

    BALANCE_SHEET_FIELDS: list[str] = [
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

    CASH_FLOW_FIELDS: list[str] = [
        "cash_f_operating_activities",
        "cash_f_operating_activities_fy",
        "cash_f_investing_activities",
        "cash_f_investing_activities_fy",
        "cash_f_financing_activities",
        "cash_f_financing_activities_fy",
        "free_cash_flow",
    ]

    MARGIN_FIELDS: list[str] = [
        "gross_margin",
        "gross_margin_percent_ttm",
        "operating_margin",
        "operating_margin_ttm",
        "pretax_margin_percent_ttm",
        "net_margin",
        "net_margin_percent_ttm",
        "EBITDA_margin",
    ]

    PROFITABILITY_FIELDS: list[str] = [
        "return_on_equity",
        "return_on_equity_fq",
        "return_on_assets",
        "return_on_assets_fq",
        "return_on_investment_ttm",
    ]

    LIQUIDITY_FIELDS: list[str] = [
        "current_ratio",
        "current_ratio_fq",
        "quick_ratio",
        "quick_ratio_fq",
    ]

    LEVERAGE_FIELDS: list[str] = [
        "debt_to_equity",
        "debt_to_equity_fq",
        "debt_to_assets",
    ]

    VALUATION_FIELDS: list[str] = [
        "market_cap_basic",
        "market_cap_calc",
        "market_cap_diluted_calc",
        "enterprise_value_fq",
        "price_earnings_ttm",
        "price_book_fq",
        "price_sales_ttm",
        "price_free_cash_flow_ttm",
    ]

    DIVIDEND_FIELDS: list[str] = [
        "dividends_yield",
        "dividends_per_share_fq",
        "dividend_payout_ratio_ttm",
    ]

    ALL_FIELDS: list[str] = (
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
    DEFAULT_COMPARISON_FIELDS: list[str] = [
        "total_revenue",
        "net_income",
        "EBITDA",
        "market_cap_basic",
        "price_earnings_ttm",
        "return_on_equity_fq",
        "debt_to_equity_fq",
    ]

    def get_fundamentals(
        self,
        exchange: str,
        symbol: str,
        fields: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get fundamental financial data for a symbol.

        Args:
            exchange: Exchange name (e.g. ``"NASDAQ"``).
            symbol: Trading symbol (e.g. ``"AAPL"``).
            fields: Specific fields to retrieve. If ``None``, retrieves all
                fields defined in ``ALL_FIELDS``.

        Returns:
            Standardized response dict with keys
            ``status``, ``data``, ``metadata``, ``error``.
        """
        field_list = fields if fields else self.ALL_FIELDS
        return self._fetch_symbol_fields(
            exchange=exchange,
            symbol=symbol,
            fields=field_list,
            data_category="fundamentals",
        )

    def compare_fundamentals(
        self,
        symbols: list[dict[str, str]],
        fields: list[str] | None = None,
    ) -> dict[str, Any]:
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
            return self._error_response(
                "No symbols provided for comparison.",
                symbols=symbols,
            )

        field_list = fields if fields else self.DEFAULT_COMPARISON_FIELDS

        all_items: list[dict[str, Any]] = []
        comparison: dict[str, dict[str, Any]] = {}

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
            cmp_meta: dict[str, Any] = {"symbols": symbols}
            if fields is not None:
                cmp_meta["fields"] = fields
            return self._error_response(
                "No data retrieved for any symbols.",
                **cmp_meta,
            )

        data: dict[str, Any] = {
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

        success_meta: dict[str, Any] = {"symbols": symbols}
        if fields is not None:
            success_meta["fields"] = fields

        return self._success_response(data, **success_meta)

    # ---- Category helpers ------------------------------------------------

    def get_income_statement(self, exchange: str, symbol: str) -> dict[str, Any]:
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

    def get_balance_sheet(self, exchange: str, symbol: str) -> dict[str, Any]:
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

    def get_cash_flow(self, exchange: str, symbol: str) -> dict[str, Any]:
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

    def get_statistics(self, exchange: str, symbol: str) -> dict[str, Any]:
        """Get statistics data for a symbol.

        Combines liquidity, leverage, and valuation fields.

        Args:
            exchange: Exchange name (e.g. ``"NASDAQ"``).
            symbol: Trading symbol (e.g. ``"AAPL"``).

        Returns:
            Statistics data including ratios and valuation metrics.
        """
        fields = self.LIQUIDITY_FIELDS + self.LEVERAGE_FIELDS + self.VALUATION_FIELDS
        return self.get_fundamentals(exchange=exchange, symbol=symbol, fields=fields)

    def get_dividends(self, exchange: str, symbol: str) -> dict[str, Any]:
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

    def get_profitability(self, exchange: str, symbol: str) -> dict[str, Any]:
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

    def get_margins(self, exchange: str, symbol: str) -> dict[str, Any]:
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
