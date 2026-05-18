"""DuckDB source_intake_snapshot helper."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from storage.db import WebIntelDB


def test_source_intake_snapshot_empty_db(tmp_path: Path) -> None:
    db_path = tmp_path / "x.duckdb"
    db = WebIntelDB(db_path)
    try:
        snap = db.source_intake_snapshot(target_date_str="2026-05-17", timezone_name="Europe/Amsterdam")
        assert snap["profiled_sources_total"] == 0
        assert snap["totals"]["discovered_today"] == 0
        assert snap["totals"]["articles_extracted_today"] == 0
        assert snap["rows"] == []
    finally:
        db.close()


def test_source_intake_snapshot_counts_window(tmp_path: Path) -> None:
    db_path = tmp_path / "y.duckdb"
    db = WebIntelDB(db_path)
    try:
        t0 = datetime(2026, 5, 17, 10, 0, tzinfo=timezone.utc)
        db.insert_discovered_url(
            {
                "id": "d1",
                "source_id": "news_ex",
                "url": "https://news.example/a",
                "discovery_method": "rss",
                "title": None,
                "published_at": None,
                "raw_metadata": "{}",
                "discovered_at": t0,
            }
        )
        db.insert_article(
            {
                "id": "a1",
                "source_id": "news_ex",
                "url": "https://news.example/a",
                "title": "t",
                "published_at": None,
                "content": "x" * 100,
                "content_length": 100,
                "content_hash": "h1",
                "language": None,
                "crawl_strategy_used": "rss_then_article_extract",
                "raw_path": None,
                "extracted_at": t0,
                "quality_score": 5.0,
            }
        )
        snap = db.source_intake_snapshot(target_date_str="2026-05-17", timezone_name="UTC")
        assert snap["totals"]["discovered_today"] >= 1
        assert snap["totals"]["articles_extracted_today"] >= 1
        by_sid = {r["source_id"]: r for r in snap["rows"]}
        assert by_sid["news_ex"]["remaining_estimate"] == 0
    finally:
        db.close()
