"""Unit tests for top-level public imports."""

import tv_scraper
from tv_scraper import CandleStreamer, ForecastStreamer, Streamer


def test_streamers_are_importable_from_package_root() -> None:
    """All public streamer classes should import from tv_scraper root."""
    assert CandleStreamer.__name__ == "CandleStreamer"
    assert ForecastStreamer.__name__ == "ForecastStreamer"
    assert Streamer.__name__ == "Streamer"


def test_streamers_are_listed_in_dunder_all() -> None:
    """Top-level exports should include all public streamer classes."""
    assert "CandleStreamer" in tv_scraper.__all__
    assert "ForecastStreamer" in tv_scraper.__all__
    assert "Streamer" in tv_scraper.__all__
