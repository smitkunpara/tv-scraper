"""Tests for Minds scraper module."""

from typing import Any, Dict, Iterator, List
from unittest.mock import MagicMock, patch

import pytest

from tv_scraper.core.base import BaseScraper
from tv_scraper.core.constants import STATUS_FAILED, STATUS_SUCCESS
from tv_scraper.scrapers.social.minds import Minds


def _sample_mind(
    uid: str = "mind123",
    text: str = "AAPL looking bullish today",
    url: str = "https://www.tradingview.com/minds/mind123",
    username: str = "testuser",
    uri: str = "/u/testuser/",
    is_broker: bool = False,
    created: str = "2025-01-07T12:00:00Z",
    symbols: Dict[str, str] | None = None,
    total_likes: int = 10,
    total_comments: int = 5,
    modified: bool = False,
    hidden: bool = False,
) -> Dict[str, Any]:
    """Build a single mind item as returned by the TradingView API."""
    if symbols is None:
        symbols = {"AAPL": "NASDAQ:AAPL"}
    return {
        "uid": uid,
        "text": text,
        "url": url,
        "author": {
            "username": username,
            "uri": uri,
            "is_broker": is_broker,
        },
        "created": created,
        "symbols": symbols,
        "total_likes": total_likes,
        "total_comments": total_comments,
        "modified": modified,
        "hidden": hidden,
    }


def _make_page_response(
    results: List[Dict[str, Any]],
    next_url: str = "",
    symbol: str = "NASDAQ:AAPL",
) -> Dict[str, Any]:
    """Build a TradingView minds API page response."""
    return {
        "results": results,
        "next": next_url,
        "meta": {
            "symbol": symbol,
            "symbols_info": {
                symbol: {
                    "short_name": symbol.split(":")[1],
                    "exchange": symbol.split(":")[0],
                }
            },
        },
    }


def _mock_response(
    json_data: Dict[str, Any],
    status_code: int = 200,
) -> MagicMock:
    """Create a mock requests.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = str(json_data)
    resp.json.return_value = json_data
    return resp


@pytest.fixture
def minds() -> Iterator[Minds]:
    """Create a Minds instance for testing."""
    yield Minds()


class TestInheritance:
    """Verify Minds inherits from BaseScraper."""

    def test_inherits_base_scraper(self) -> None:
        """Minds must be a subclass of BaseScraper."""
        assert issubclass(Minds, BaseScraper)


class TestGetMindsSuccess:
    """Tests for successful minds retrieval."""

    @patch("tv_scraper.core.base.BaseScraper._make_request")
    def test_get_minds_success(self, mock_get: MagicMock, minds: Minds) -> None:
        """Single page success returns standard envelope with parsed data."""
        mock_get.return_value = _mock_response(
            _make_page_response([_sample_mind()])
        )

        result = minds.get_minds(exchange="NASDAQ", symbol="AAPL")

        assert result["status"] == STATUS_SUCCESS
        assert result["error"] is None
        assert len(result["data"]) == 1

        mind = result["data"][0]
        # Should contain these fields
        assert mind["text"] == "AAPL looking bullish today"
        assert mind["author"]["username"] == "testuser"
        assert mind["total_likes"] == 10
        assert mind["total_comments"] == 5
        # Should NOT contain these fields (removed as per requirements)
        assert "uid" not in mind
        assert "symbols" not in mind
        assert "modified" not in mind
        assert "hidden" not in mind

    @patch("tv_scraper.core.base.BaseScraper._make_request")
    def test_get_minds_with_limit(self, mock_get: MagicMock, minds: Minds) -> None:
        """Limit parameter truncates results to at most that many items."""
        items = [_sample_mind(uid=f"m{i}") for i in range(5)]
        mock_get.return_value = _mock_response(
            _make_page_response(items)
        )

        result = minds.get_minds(exchange="NASDAQ", symbol="AAPL", limit=3)

        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) == 3

    @patch("tv_scraper.core.base.BaseScraper._make_request")
    def test_get_minds_pagination(self, mock_get: MagicMock, minds: Minds) -> None:
        """Multi-page cursor-based pagination follows next URL."""
        page1 = _make_page_response(
            [_sample_mind(uid="m1")],
            next_url="https://www.tradingview.com/api/v1/minds/?c=cursor_abc",
        )
        page2 = _make_page_response(
            [_sample_mind(uid="m2")],
            next_url="",
        )

        mock_get.side_effect = [
            _mock_response(page1),
            _mock_response(page2),
        ]

        result = minds.get_minds(exchange="NASDAQ", symbol="AAPL")

        assert result["status"] == STATUS_SUCCESS
        assert len(result["data"]) == 2
        assert result["metadata"]["pages"] == 2
        assert mock_get.call_count == 2

    @patch("tv_scraper.core.base.BaseScraper._make_request")
    def test_get_minds_no_data(self, mock_get: MagicMock, minds: Minds) -> None:
        """Empty results returns success with empty list."""
        mock_get.return_value = _mock_response(
            _make_page_response([])
        )

        result = minds.get_minds(exchange="NASDAQ", symbol="AAPL")

        assert result["status"] == STATUS_SUCCESS
        assert result["data"] == []
        assert result["error"] is None


class TestGetMindsErrors:
    """Tests for error handling — returns error responses, never raises."""

    def test_get_minds_invalid_exchange(self, minds: Minds) -> None:
        """Invalid exchange returns error response."""
        result = minds.get_minds(exchange="FAKEXCHANGE", symbol="AAPL")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None
        assert "exchange" in result["error"].lower() or "invalid" in result["error"].lower()

    def test_get_minds_empty_symbol(self, minds: Minds) -> None:
        """Empty symbol returns error response."""
        result = minds.get_minds(exchange="NASDAQ", symbol="")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None

    @patch("tv_scraper.core.base.BaseScraper._make_request")
    def test_get_minds_network_error(self, mock_get: MagicMock, minds: Minds) -> None:
        """Network failure returns error response, does not raise."""
        mock_get.side_effect = Exception("Connection refused")

        result = minds.get_minds(exchange="NASDAQ", symbol="AAPL")

        assert result["status"] == STATUS_FAILED
        assert result["data"] is None
        assert result["error"] is not None


class TestParseMind:
    """Tests for the internal _parse_mind method."""

    def test_parse_mind_extracts_fields(self, minds: Minds) -> None:
        """_parse_mind extracts and normalizes expected fields (excluding removed fields)."""
        raw = _sample_mind(
            uid="uid42",
            text="Buy signal",
            url="https://example.com",
            username="analyst",
            uri="/u/analyst/",
            is_broker=True,
            created="2025-06-15T08:30:00Z",
            symbols={"BTC": "BINANCE:BTCUSD", "ETH": "BINANCE:ETHUSDT"},
            total_likes=99,
            total_comments=15,
            modified=True,
            hidden=False,
        )

        parsed = minds._parse_mind(raw)

        # Should contain these fields
        assert parsed["text"] == "Buy signal"
        assert parsed["url"] == "https://example.com"
        assert parsed["author"]["username"] == "analyst"
        assert parsed["author"]["profile_url"] == "https://www.tradingview.com/u/analyst/"
        assert parsed["author"]["is_broker"] is True
        assert parsed["created"] == "2025-06-15 08:30:00"
        assert parsed["total_likes"] == 99
        assert parsed["total_comments"] == 15
        # Should NOT contain these removed fields
        assert "uid" not in parsed
        assert "symbols" not in parsed
        assert "modified" not in parsed
        assert "hidden" not in parsed

    def test_parse_mind_invalid_date(self, minds: Minds) -> None:
        """_parse_mind handles invalid date without raising."""
        raw = _sample_mind(created="not-a-date")
        parsed = minds._parse_mind(raw)
        assert parsed["created"] == "not-a-date"


class TestResponseFormat:
    """Tests for response envelope structure."""

    @patch("tv_scraper.core.base.BaseScraper._make_request")
    def test_response_has_standard_envelope(
        self, mock_get: MagicMock, minds: Minds
    ) -> None:
        """Response contains exactly status/data/metadata/error keys."""
        mock_get.return_value = _mock_response(
            _make_page_response([_sample_mind()])
        )

        result = minds.get_minds(exchange="NASDAQ", symbol="AAPL")

        assert set(result.keys()) == {"status", "data", "metadata", "error"}

    @patch("tv_scraper.core.base.BaseScraper._make_request")
    def test_separate_exchange_symbol_params(
        self, mock_get: MagicMock, minds: Minds
    ) -> None:
        """Exchange and symbol are separate params, combined internally."""
        mock_get.return_value = _mock_response(
            _make_page_response(
                [_sample_mind()],
                symbol="NYSE:TSLA",
            )
        )

        result = minds.get_minds(exchange="NYSE", symbol="TSLA")

        assert result["status"] == STATUS_SUCCESS

        # Verify the API was called with the combined symbol
        call_kwargs = mock_get.call_args
        params = call_kwargs.kwargs.get("params") or call_kwargs[1].get("params", {})
        assert params.get("symbol") == "NYSE:TSLA"
