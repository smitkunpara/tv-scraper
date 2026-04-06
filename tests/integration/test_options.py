"""Integration tests for Options scraper.

Tests cross-module workflows and integration with other tv_scraper components.
"""

from unittest.mock import MagicMock, patch

import pytest

from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.scrapers.market_data.fundamentals import Fundamentals
from tv_scraper.scrapers.market_data.options import Options
from tv_scraper.scrapers.screening.screener import Screener


@pytest.fixture
def options_scraper() -> Options:
    """Create an Options scraper instance."""
    return Options()


@pytest.fixture
def fundamentals_scraper() -> Fundamentals:
    """Create a Fundamentals scraper instance."""
    return Fundamentals()


@pytest.fixture
def screener_scraper() -> Screener:
    """Create a Screener scraper instance."""
    return Screener()


class TestOptionsWithOtherScrapers:
    """Test Options works alongside other scrapers."""

    @patch.object(Options, "_request")
    def test_options_after_fundamentals(
        self, mock_options_request: MagicMock, options_scraper: Options
    ) -> None:
        """Verify Options can be used after Fundamentals."""
        mock_options_request.return_value = (
            {
                "fields": ["strike"],
                "symbols": [{"s": "TEST", "f": [200]}],
                "totalCount": 1,
            },
            None,
        )

        with patch(
            "tv_scraper.core.validators.DataValidator.verify_options_symbol",
            return_value=("NASDAQ", "AAPL"),
        ):
            result = options_scraper.get_options_by_strike(
                exchange="NASDAQ",
                symbol="AAPL",
                strike=200,
            )

        assert result["status"] == STATUS_SUCCESS

    @patch.object(Options, "_request")
    def test_multiple_options_calls_with_different_symbols(
        self, mock_request: MagicMock, options_scraper: Options
    ) -> None:
        """Verify multiple Options calls with different symbols."""

        def mock_request_side_effect(*args, **kwargs):
            json_payload = kwargs.get("json_payload", {})
            index_filters = json_payload.get("index_filters", [])
            underlying = index_filters[0]["values"][0] if index_filters else ""

            if "AAPL" in underlying:
                return (
                    {
                        "fields": ["strike", "bid", "ask"],
                        "symbols": [
                            {"s": "NASDAQ:AAPL240419C00200000", "f": [200, 5.0, 5.1]},
                        ],
                        "totalCount": 1,
                    },
                    None,
                )
            elif "MSFT" in underlying:
                return (
                    {
                        "fields": ["strike", "bid", "ask"],
                        "symbols": [
                            {"s": "NASDAQ:MSFT240419C00400000", "f": [400, 10.0, 10.2]},
                        ],
                        "totalCount": 1,
                    },
                    None,
                )
            return (None, "Unknown symbol"), "Unknown symbol"

        mock_request.side_effect = mock_request_side_effect

        with patch(
            "tv_scraper.core.validators.DataValidator.verify_options_symbol",
            side_effect=lambda e, s: (e.upper(), s.upper()),
        ):
            result_aapl = options_scraper.get_options_by_strike(
                exchange="NASDAQ", symbol="AAPL", strike=200
            )
            result_msft = options_scraper.get_options_by_strike(
                exchange="NASDAQ", symbol="MSFT", strike=400
            )

        assert result_aapl["status"] == STATUS_SUCCESS
        assert result_msft["status"] == STATUS_SUCCESS
        assert result_aapl["metadata"]["symbol"] == "AAPL"
        assert result_msft["metadata"]["symbol"] == "MSFT"


class TestOptionsWorkflowScenarios:
    """Test real-world workflow scenarios."""

    @patch.object(Options, "_request")
    def test_options_chain_workflow(
        self, mock_request: MagicMock, options_scraper: Options
    ) -> None:
        """Test a typical options chain workflow: get by expiry then by strike."""

        def mock_side_effect(*args, **kwargs):
            json_payload = kwargs.get("json_payload", {})
            filters = json_payload.get("filter", [])

            for f in filters:
                if f.get("left") == "expiration":
                    return (
                        {
                            "fields": [
                                "expiration",
                                "strike",
                                "bid",
                                "ask",
                                "root",
                                "delta",
                            ],
                            "symbols": [
                                {
                                    "s": "BSE:SENSEX240419C083000",
                                    "f": [20260419, 83000, 500, 510, "BSX", 0.5],
                                },
                                {
                                    "s": "BSE:SENSEX240419P083000",
                                    "f": [20260419, 83000, 100, 110, "BSX", -0.5],
                                },
                                {
                                    "s": "BSE:SENSEX240419C084000",
                                    "f": [20260419, 84000, 300, 310, "BSX", 0.4],
                                },
                                {
                                    "s": "BSE:SENSEX240419P084000",
                                    "f": [20260419, 84000, 150, 160, "BSX", -0.4],
                                },
                            ],
                            "totalCount": 4,
                        },
                        None,
                    )
            return (
                {
                    "fields": ["strike", "bid", "ask", "delta"],
                    "symbols": [
                        {"s": "BSE:SENSEX240419C083000", "f": [83000, 500, 510, 0.5]},
                    ],
                    "totalCount": 1,
                },
                None,
            )

        mock_request.side_effect = mock_side_effect

        with patch(
            "tv_scraper.core.validators.DataValidator.verify_options_symbol",
            return_value=("BSE", "SENSEX"),
        ):
            expiry_result = options_scraper.get_options_by_expiry(
                exchange="BSE",
                symbol="SENSEX",
                expiration=20260419,
                root="BSX",
            )

        assert expiry_result["status"] == STATUS_SUCCESS
        assert len(expiry_result["data"]) == 4

        strikes = {opt["strike"] for opt in expiry_result["data"]}
        assert 83000 in strikes
        assert 84000 in strikes

    @patch.object(Options, "_request")
    def test_itm_otm_options_filtering(
        self, mock_request: MagicMock, options_scraper: Options
    ) -> None:
        """Test filtering ITM vs OTM options using delta values."""
        mock_request.return_value = (
            {
                "fields": ["strike", "delta", "bid", "ask"],
                "symbols": [
                    {"s": "T1", "f": [190, 0.8, 15.0, 15.5]},  # Deep ITM call
                    {"s": "T2", "f": [200, 0.5, 8.0, 8.2]},  # ATM call
                    {"s": "T3", "f": [210, 0.2, 3.0, 3.1]},  # OTM call
                    {"s": "T4", "f": [220, 0.05, 0.8, 0.9]},  # Deep OTM call
                ],
                "totalCount": 4,
            },
            None,
        )

        with patch(
            "tv_scraper.core.validators.DataValidator.verify_options_symbol",
            return_value=("NASDAQ", "AAPL"),
        ):
            result = options_scraper.get_options_by_strike(
                exchange="NASDAQ",
                symbol="AAPL",
                strike=200,
            )

        assert result["status"] == STATUS_SUCCESS
        itm_calls = [opt for opt in result["data"] if opt.get("delta", 0) > 0.5]
        assert len(itm_calls) >= 1


class TestOptionsWithValidationIntegration:
    """Test Options with DataValidator integration."""

    @patch("tv_scraper.core.validators.DataValidator.verify_options_symbol")
    def test_validation_called_before_request(
        self, mock_verify, options_scraper: Options
    ) -> None:
        """Verify validation is called before making the request."""
        mock_verify.return_value = ("BSE", "SENSEX")

        with patch.object(Options, "_request") as mock_request:
            mock_request.return_value = (
                {
                    "fields": ["strike"],
                    "symbols": [{"s": "TEST", "f": [83000]}],
                    "totalCount": 1,
                },
                None,
            )

            options_scraper.get_options_by_strike(
                exchange="BSE",
                symbol="SENSEX",
                strike=83000,
            )

            mock_verify.assert_called_once_with("BSE", "SENSEX")
            mock_request.assert_called_once()

    @patch("tv_scraper.core.validators.DataValidator.verify_options_symbol")
    def test_request_skipped_on_validation_failure(
        self, mock_verify, options_scraper: Options
    ) -> None:
        """Verify no request is made if validation fails."""
        from tv_scraper.core.exceptions import ValidationError

        mock_verify.side_effect = ValidationError("Invalid exchange")

        with patch.object(Options, "_request") as mock_request:
            result = options_scraper.get_options_by_strike(
                exchange="INVALID",
                symbol="INVALID",
                strike=100,
            )

            mock_request.assert_not_called()
            assert result["status"] == "failed"


class TestOptionsErrorRecovery:
    """Test error recovery scenarios."""

    @patch.object(Options, "_request")
    def test_retry_after_network_error(
        self, mock_request: MagicMock, options_scraper: Options
    ) -> None:
        """Verify the scraper can handle transient network errors."""
        call_count = 0

        def mock_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return (None, "Connection reset by peer")
            return (
                {
                    "fields": ["strike"],
                    "symbols": [{"s": "TEST", "f": [200]}],
                    "totalCount": 1,
                },
                None,
            )

        mock_request.side_effect = mock_side_effect

        with patch(
            "tv_scraper.core.validators.DataValidator.verify_options_symbol",
            return_value=("NASDAQ", "AAPL"),
        ):
            result = options_scraper.get_options_by_strike(
                exchange="NASDAQ",
                symbol="AAPL",
                strike=200,
            )

        assert result["status"] == STATUS_FAILED
        assert "Connection reset" in result["error"]


class TestOptionsDataIntegrity:
    """Test data integrity across requests."""

    @patch.object(Options, "_request")
    def test_data_not_mutated_between_calls(
        self, mock_request: MagicMock, options_scraper: Options
    ) -> None:
        """Verify data from one call is not mutated by subsequent calls."""
        responses = [
            {
                "fields": ["strike", "bid", "ask"],
                "symbols": [{"s": "T1", "f": [100, 5.0, 5.1]}],
                "totalCount": 1,
            },
            {
                "fields": ["strike", "bid", "ask"],
                "symbols": [{"s": "T2", "f": [200, 10.0, 10.2]}],
                "totalCount": 1,
            },
        ]
        mock_request.side_effect = [
            (responses[0], None),
            (responses[1], None),
        ]

        with patch(
            "tv_scraper.core.validators.DataValidator.verify_options_symbol",
            side_effect=lambda e, s: (e.upper(), s.upper()),
        ):
            result1 = options_scraper.get_options_by_strike(
                exchange="NASDAQ", symbol="AAPL", strike=100
            )
            result2 = options_scraper.get_options_by_strike(
                exchange="NASDAQ", symbol="MSFT", strike=200
            )

        assert result1["data"][0]["strike"] == 100
        assert result2["data"][0]["strike"] == 200


class TestOptionsExportIntegration:
    """Test export integration with Options scraper."""

    @patch.object(Options, "_request")
    @patch("tv_scraper.core.base.save_json_file")
    def test_export_includes_metadata(
        self,
        mock_save: MagicMock,
        mock_request: MagicMock,
        options_scraper: Options,
    ) -> None:
        """Verify exported data includes proper metadata."""
        mock_request.return_value = (
            {
                "fields": ["strike", "bid", "ask"],
                "symbols": [{"s": "TEST", "f": [200, 5.0, 5.1]}],
                "totalCount": 1,
            },
            None,
        )

        with patch(
            "tv_scraper.core.validators.DataValidator.verify_options_symbol",
            return_value=("NASDAQ", "AAPL"),
        ):
            options_scraper.export_result = True
            options_scraper.get_options_by_strike(
                exchange="NASDAQ",
                symbol="AAPL",
                strike=200,
            )

        assert mock_save.called
        call_args = mock_save.call_args
        saved_data = call_args[0][0]
        assert isinstance(saved_data, list)
        assert len(saved_data) == 1


class TestOptionsConcurrency:
    """Test concurrent usage of Options scraper."""

    @patch.object(Options, "_request")
    def test_sequential_calls_independent(
        self, mock_request: MagicMock, options_scraper: Options
    ) -> None:
        """Verify sequential calls are independent."""
        responses = [
            (
                {
                    "fields": ["strike"],
                    "symbols": [{"s": f"T{i}", "f": [i * 100]}],
                    "totalCount": 1,
                },
                None,
            )
            for i in range(1, 4)
        ]
        mock_request.side_effect = responses

        with patch(
            "tv_scraper.core.validators.DataValidator.verify_options_symbol",
            side_effect=lambda e, s: (e.upper(), s.upper()),
        ):
            results = []
            for i, strike in enumerate([100, 200, 300], 1):
                result = options_scraper.get_options_by_strike(
                    exchange="NASDAQ",
                    symbol=f"SYM{i}",
                    strike=strike,
                )
                results.append(result)

        assert all(r["status"] == STATUS_SUCCESS for r in results)
        assert results[0]["data"][0]["strike"] == 100
        assert results[1]["data"][0]["strike"] == 200
        assert results[2]["data"][0]["strike"] == 300


class TestOptionsBSEIntegration:
    """Test BSE-specific options integration."""

    @patch.object(Options, "_request")
    def test_bse_sensex_options_flow(
        self, mock_request: MagicMock, options_scraper: Options
    ) -> None:
        """Test BSE SENSEX options fetching workflow."""
        mock_request.return_value = (
            {
                "fields": [
                    "expiration",
                    "strike",
                    "bid",
                    "ask",
                    "root",
                    "delta",
                    "gamma",
                    "theta",
                    "vega",
                ],
                "symbols": [
                    {
                        "s": "BSE:SENSEX240419C083000",
                        "f": [20260419, 83000, 500, 510, "BSX", 0.5, 0.01, -0.05, 0.2],
                    },
                    {
                        "s": "BSE:SENSEX240419P083000",
                        "f": [20260419, 83000, 100, 110, "BSX", -0.5, 0.01, 0.05, 0.2],
                    },
                ],
                "totalCount": 2,
            },
            None,
        )

        with patch(
            "tv_scraper.core.validators.DataValidator.verify_options_symbol",
            return_value=("BSE", "SENSEX"),
        ):
            result = options_scraper.get_options_by_expiry(
                exchange="BSE",
                symbol="SENSEX",
                expiration=20260419,
                root="BSX",
            )

        assert result["status"] == STATUS_SUCCESS
        assert result["metadata"]["exchange"] == "BSE"
        assert result["metadata"]["symbol"] == "SENSEX"
        assert result["metadata"]["filter_value"] == 20260419
