"""Tests for today full-article crawl helpers and exports."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

import feedparser
import pytest

from reporting.crawl_report import write_today_crawl_report
from scrapy_engine.spiders import sitemap_article_spider as smod
from storage.db import WebIntelDB
from utils.today_filter import (
    is_datetime_in_range,
    is_url_likely_today,
    parse_any_datetime,
    resolve_calendar_date,
    target_date_range,
)


def test_parse_rss_entry_today() -> None:
    xml = """<?xml version="1.0"?><rss><channel><item><title>t</title>
    <link>https://example.com/news/2026/05/17/a</link>
    <pubDate>Sun, 17 May 2026 08:00:00 GMT</pubDate></item></channel></rss>"""
    parsed = feedparser.parse(xml.encode())
    entry = parsed.entries[0]
    dt = parse_any_datetime(entry.get("published"))
    assert dt is not None
    start, end = target_date_range("2026-05-17", "Europe/Amsterdam")
    assert is_datetime_in_range(dt, start, end)


def test_sitemap_lastmod_today_filter() -> None:
    body = b"""<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>https://ex.com/old</loc><lastmod>2020-01-01</lastmod></url>
      <url><loc>https://ex.com/new</loc><lastmod>2026-05-17</lastmod></url>
    </urlset>"""
    pairs = smod._iter_sitemap_pairs(body)
    locs = [p[0] for p in pairs]
    assert "https://ex.com/new" in locs
    lm = next(p[1] for p in pairs if p[0].endswith("/new"))
    dt = parse_any_datetime(lm or "")
    assert dt is not None
    start, end = target_date_range("2026-05-17", "UTC")
    assert is_datetime_in_range(dt, start, end)


def test_url_likely_today() -> None:
    d = date(2026, 5, 17)
    assert is_url_likely_today("https://news.example.com/2026/05/17/world/a", d)
    assert is_url_likely_today("https://news.example.com/2026-05-17/foo", d)
    assert not is_url_likely_today("https://news.example.com/2026/05/16/foo", d)


def test_today_export_empty_db_no_crash(tmp_path: Path) -> None:
    db_path = tmp_path / "w.duckdb"
    db = WebIntelDB(db_path)
    try:
        db.export_today_articles_csv(tmp_path / "a.csv", target_date_str="2026-05-17", timezone_name="Europe/Amsterdam")
        db.export_today_articles_metadata_csv(
            tmp_path / "meta.csv", target_date_str="2026-05-17", timezone_name="Europe/Amsterdam"
        )
        db.export_today_articles_parquet(tmp_path / "a.parquet", target_date_str="2026-05-17", timezone_name="Europe/Amsterdam")
        db.export_today_errors_csv(tmp_path / "e.csv", target_date_str="2026-05-17", timezone_name="Europe/Amsterdam")
        db.export_today_frontier_csv(tmp_path / "f.csv", target_date_str="2026-05-17", timezone_name="Europe/Amsterdam")
        db.export_today_source_health_csv(tmp_path / "h.csv", target_date_str="2026-05-17", timezone_name="Europe/Amsterdam")
    finally:
        db.close()
    assert (tmp_path / "a.csv").is_file()
    assert (tmp_path / "meta.csv").is_file()
    meta_header = (tmp_path / "meta.csv").read_text(encoding="utf-8").strip().split("\n")[0]
    assert meta_header == "source_id,title,published_at,url,content_length,quality_score,crawl_strategy_used"


def test_today_report_empty_db(tmp_path: Path) -> None:
    db_path = tmp_path / "w.duckdb"
    db = WebIntelDB(db_path)
    report = tmp_path / "today_final_report.md"
    try:
        write_today_crawl_report(db, report, target_date="2026-05-17", timezone_name="Europe/Amsterdam")
    finally:
        db.close()
    text = report.read_text(encoding="utf-8")
    assert "Today Crawl Report" in text
    assert "Europe/Amsterdam" in text


def test_run_today_command_building() -> None:
    from run_today import build_today_commands

    cmds = build_today_commands(
        python_executable="python",
        input_path=Path("config/sources_raw.txt"),
        profile_limit=198,
        strategy="rss",
        force_refresh=True,
        run_id="rid",
        date_arg="today",
        timezone_arg="Europe/Amsterdam",
        max_urls_per_source=500,
        close_spider_timeout=900,
    )
    assert "run_profile.py" in cmds[0][1]
    assert "--today-only" in cmds[1]
    assert cmds[1][cmds[1].index("--run-id") + 1] == "rid"
    assert "--today-only" in cmds[2]


def test_resolve_calendar_date_explicit() -> None:
    assert resolve_calendar_date("2026-05-17", "Europe/Amsterdam") == date(2026, 5, 17)
