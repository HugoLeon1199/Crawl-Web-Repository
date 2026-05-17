"""Minimal tests for Scrapy scaffold (loader, settings, pipeline guards)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb
import pytest
import scrapy
from scrapy.settings import Settings

from scrapy_engine.db_source_loader import load_sources_for_scrapy
from scrapy_engine.items import ArticleItem
from scrapy_engine.pipelines import WebIntelArticlePipeline
from scrapy_engine.runner import ScrapyRunSummary
from scrapy_engine.settings import build_scrapy_settings_dict
from settings import CrawlRules
from storage.db import DDL, WebIntelDB


def _profile_row(**kwargs: Any) -> dict[str, Any]:
    base = {
        "source_id": "a_com",
        "input_url": "https://a.com/",
        "normalized_url": "https://a.com/",
        "domain": "a.com",
        "scheme": "https",
        "homepage_url": "https://a.com/",
        "robots_url": None,
        "robots_ok": True,
        "robots_sitemaps": "[]",
        "robots_disallow_detected": False,
        "robots_can_fetch_homepage": True,
        "has_known_api": False,
        "known_api_adapter": None,
        "known_api_endpoint_hint": None,
        "has_rss": True,
        "rss_urls": json.dumps(["https://a.com/feed.xml"]),
        "rss_valid_count": 1,
        "has_sitemap": False,
        "sitemap_urls": json.dumps([]),
        "sitemap_url_count": 0,
        "html_status_code": 200,
        "html_title": "t",
        "html_text_length": 100,
        "html_link_count": 5,
        "html_extract_ok": False,
        "sample_extracted_text_length": 0,
        "js_required": False,
        "paywall_detected": False,
        "captcha_detected": False,
        "login_detected": False,
        "best_strategy": "rss_then_article_extract",
        "tos_risk": None,
        "status": "active",
        "error_message": None,
        "profiled_at": datetime.now(timezone.utc),
    }
    merged = {**base, **kwargs}
    return merged


def _seed_db(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(path))
    try:
        conn.execute(DDL)
        for r in rows:
            cols = ", ".join(r.keys())
            ph = ", ".join(["?" for _ in r])
            conn.execute(f"INSERT OR REPLACE INTO source_profiles ({cols}) VALUES ({ph})", list(r.values()))
    finally:
        conn.close()


def test_db_source_loader_filters_strategy(tmp_path: Path) -> None:
    db_path = tmp_path / "web_intel.duckdb"
    rows = [
        _profile_row(source_id="rss_ok", best_strategy="rss_then_article_extract", status="active"),
        _profile_row(
            source_id="api_skip",
            best_strategy="api_first",
            status="active",
            rss_urls=json.dumps(["https://api.example/feed"]),
        ),
        _profile_row(
            source_id="meta_skip",
            best_strategy="metadata_only",
            status="active",
        ),
        _profile_row(
            source_id="html_wall",
            best_strategy="html_then_trafilatura",
            status="active",
            rss_urls=json.dumps([]),
            homepage_url="https://wall.example/",
            robots_can_fetch_homepage=False,
        ),
        _profile_row(
            source_id="html_ok",
            best_strategy="html_then_trafilatura",
            status="active_candidate",
            rss_urls=json.dumps([]),
            homepage_url="https://html.example/",
            robots_can_fetch_homepage=True,
        ),
        _profile_row(
            source_id="sm_ok",
            best_strategy="sitemap_then_article_extract",
            status="active",
            rss_urls=json.dumps([]),
            sitemap_urls=json.dumps(["https://sm.example/sitemap.xml"]),
        ),
    ]

    _seed_db(db_path, rows)

    rss_b = load_sources_for_scrapy(db_path, "rss", limit=50)["rss"]
    assert [r["source_id"] for r in rss_b] == ["rss_ok"]

    html_b = load_sources_for_scrapy(db_path, "html", limit=50)["html"]
    ids = {r["source_id"] for r in html_b}
    assert "html_ok" in ids and "html_wall" not in ids

    sm_b = load_sources_for_scrapy(db_path, "sitemap", limit=50)["sitemap"]
    assert [r["source_id"] for r in sm_b] == ["sm_ok"]


def test_scrapy_settings_robots_obey_true(tmp_path: Path) -> None:
    rules = CrawlRules()
    d = build_scrapy_settings_dict(
        rules,
        db_path=tmp_path / "db.duckdb",
        crawl_rules_path=tmp_path / "c.yaml",
        raw_root=tmp_path / "raw",
        summary=ScrapyRunSummary(),
    )
    assert d["ROBOTSTXT_OBEY"] is True
    assert d["USER_AGENT"] == rules.user_agent
    assert d["DOWNLOAD_TIMEOUT"] == int(rules.request_timeout_seconds)
    assert d["CONCURRENT_REQUESTS_PER_DOMAIN"] == 2


@pytest.fixture
def pipeline_env(tmp_path: Path) -> tuple[WebIntelArticlePipeline, Path]:
    db_path = tmp_path / "web_intel.duckdb"
    rules_path = tmp_path / "crawl_rules.yaml"
    raw_root = tmp_path / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    rules_path.write_text(
        "\n".join(
            [
                'user_agent: "TestBot/0.1"',
                "request_timeout_seconds: 15",
                "max_retries: 1",
                "default_delay_seconds: 1",
                "min_article_content_length: 300",
                "paywall_keywords:",
                "  - subscribe",
                "login_keywords:",
                "  - log in",
                "captcha_keywords:",
                "  - captcha",
            ]
        ),
        encoding="utf-8",
    )
    WebIntelDB(db_path)

    st = Settings()
    st.setdict(
        {
            "WEB_INTEL_DB_PATH": str(db_path.resolve()),
            "WEB_INTEL_CRAWL_RULES_PATH": str(rules_path.resolve()),
            "WEB_INTEL_RAW_ROOT": str(raw_root.resolve()),
            "WEB_INTEL_SUMMARY": ScrapyRunSummary(),
            "WEB_INTEL_MIN_ARTICLE_LENGTH": 300,
        },
        priority="cmdline",
    )

    class FakeCrawler:
        def __init__(self, settings: Settings) -> None:
            self.settings = settings

    pipe = WebIntelArticlePipeline.from_crawler(FakeCrawler(st))
    pipe.open_spider(scrapy.Spider(name="test"))
    return pipe, db_path


def test_pipeline_blocks_access_control(pipeline_env: tuple[WebIntelArticlePipeline, Path]) -> None:
    pipe, db_path = pipeline_env
    item = ArticleItem(
        source_id="s1",
        url="https://example.com/a",
        crawl_strategy_used="rss_then_article_extract",
        html_body="<html><body>please subscribe now</body></html>",
        response_status=200,
        source_active=True,
    )
    pipe.process_item(item, scrapy.Spider(name="test"))

    db = duckdb.connect(str(db_path), read_only=True)
    try:
        errs = db.execute("SELECT error_type FROM crawl_errors").fetchall()
        arts = db.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    finally:
        db.close()
    assert arts == 0
    assert any(row[0] == "AccessControlDetected" for row in errs)


def test_pipeline_short_content_to_crawl_errors(pipeline_env: tuple[WebIntelArticlePipeline, Path]) -> None:
    pipe, db_path = pipeline_env
    item = ArticleItem(
        source_id="s2",
        url="https://example.com/b",
        crawl_strategy_used="html_then_trafilatura",
        html_body="<html><body><p>hi</p></body></html>",
        response_status=200,
        source_active=True,
    )
    pipe.process_item(item, scrapy.Spider(name="test"))

    db = duckdb.connect(str(db_path), read_only=True)
    try:
        types = {r[0] for r in db.execute("SELECT error_type FROM crawl_errors").fetchall()}
        arts = db.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    finally:
        db.close()
    assert arts == 0
    assert "ShortContent" in types
