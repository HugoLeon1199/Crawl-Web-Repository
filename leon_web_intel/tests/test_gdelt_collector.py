"""Unit tests for GDELT helper functions (no network)."""

from __future__ import annotations

from collectors.gdelt_collector import normalize_gdelt_query, url_to_gdelt_source_id


def test_normalize_gdelt_query_star() -> None:
    assert normalize_gdelt_query("*") == "*"
    assert normalize_gdelt_query("") == "*"


def test_url_to_gdelt_source_id() -> None:
    assert url_to_gdelt_source_id("https://www.BBC.co.uk/news") == "gdelt_bbc_co_uk"
