"""Fundamentals scraper for fetching financial data from TradingView."""

from typing import Any

from tv_scraper.core.base import catch_errors
from tv_scraper.core.exceptions import ValidationError
from tv_scraper.core.scanner import ScannerScraper
from tv_scraper.core.validation_data import EXCHANGE_LITERAL


class Fundamentals(ScannerScraper):
    """Scraper for fundamental financial data from TradingView.

    Fetches income statement, balance sheet, cash flow, margins, profitability,
    liquidity, leverage, valuation, and dividend data via the TradingView
    scanner API.

    Args:
        export: Export format, ``"json"`` or ``"csv"``.
            If ``None`` (default), results are not exported.
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

    @catch_errors
    def get_fundamentals(
        self,
        exchange: EXCHANGE_LITERAL,
        symbol: str,
        fields: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get fundamental financial data for a symbol.

        Args:
            exchange: Exchange name (e.g. ``"NASDAQ"``).
            symbol: Trading symbol (e.g. ``"AAPL"``).
            fields: Specific fields to retrieve. If ``None`` or an empty
                list, retrieves all fields defined in ``ALL_FIELDS``.

        Returns:
            Standardized response dict with keys
            ``status``, ``data``, ``metadata``, ``error``.
        """
        if fields is not None and not isinstance(fields, list):
            raise ValidationError("Fields must be a list of strings or None.")

        field_list = fields if fields else self.ALL_FIELDS
        self._validate_list(field_list, self.ALL_FIELDS)

        return self._fetch_symbol_fields(
            exchange=exchange,
            symbol=symbol,
            fields=field_list,
            data_category="fundamentals",
        )
