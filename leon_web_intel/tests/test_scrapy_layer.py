"""Minimal tests for Scrapy scaffold (loader, settings, pipeline guards)."""

from __future__ import annotations

import json
from collections.abc import Generator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb
import pytest
import scrapy
from scrapy import Request
from scrapy.http import HtmlResponse
from scrapy.settings import Settings

from scrapy_engine.db_source_loader import load_sources_for_scrapy
from scrapy_engine.items import ArticleItem
from scrapy_engine.pipelines import WebIntelArticlePipeline
from scrapy_engine.runner import ScrapyRunSummary
from scrapy_engine.settings import build_scrapy_settings_dict
from scrapy_engine.spiders.html_article_spider import HtmlArticleSpider
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
    assert d["CLOSESPIDER_TIMEOUT"] == 600
    assert d["WEB_INTEL_TODAY_ONLY"] is False
    assert d["WEB_INTEL_TARGET_DATE"] == "today"
    assert d["WEB_INTEL_TIMEZONE"] == "Europe/Amsterdam"


def test_scrapy_settings_closespider_timeout_override(tmp_path: Path) -> None:
    rules = CrawlRules()
    d = build_scrapy_settings_dict(
        rules,
        db_path=tmp_path / "db.duckdb",
        crawl_rules_path=tmp_path / "c.yaml",
        raw_root=tmp_path / "raw",
        summary=ScrapyRunSummary(),
        closespider_timeout=42,
    )
    assert d["CLOSESPIDER_TIMEOUT"] == 42


@pytest.fixture
def pipeline_env(tmp_path: Path) -> Generator[tuple[WebIntelArticlePipeline, Path, Settings], None, None]:
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
    _db_init = WebIntelDB(db_path)
    _db_init.close()

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
    spider = scrapy.Spider(name="test")
    pipe.open_spider(spider)
    try:
        yield pipe, db_path, st
    finally:
        pipe.close_spider(spider)


def test_pipeline_blocks_access_control(pipeline_env: tuple[WebIntelArticlePipeline, Path, Settings]) -> None:
    pipe, db_path, settings = pipeline_env
    spider = scrapy.Spider(name="test")
    spider.settings = settings
    item = ArticleItem(
        source_id="s1",
        url="https://example.com/a",
        crawl_strategy_used="rss_then_article_extract",
        html_body="<html><body>please subscribe now</body></html>",
        response_status=200,
        source_active=True,
    )
    pipe.process_item(item, spider)
    pipe.close_spider(spider)

    db = duckdb.connect(str(db_path))
    try:
        errs = db.execute("SELECT error_type FROM crawl_errors").fetchall()
        arts = db.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    finally:
        db.close()
    assert arts == 0
    assert any(row[0] == "AccessControlDetected" for row in errs)


def test_pipeline_short_content_to_crawl_errors(pipeline_env: tuple[WebIntelArticlePipeline, Path, Settings]) -> None:
    pipe, db_path, settings = pipeline_env
    spider = scrapy.Spider(name="test")
    spider.settings = settings
    item = ArticleItem(
        source_id="s2",
        url="https://example.com/b",
        crawl_strategy_used="html_then_trafilatura",
        html_body="<html><body><p>hi</p></body></html>",
        response_status=200,
        source_active=True,
    )
    pipe.process_item(item, spider)
    pipe.close_spider(spider)

    db = duckdb.connect(str(db_path))
    try:
        types = {r[0] for r in db.execute("SELECT error_type FROM crawl_errors").fetchall()}
        arts = db.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    finally:
        db.close()
    assert arts == 0
    assert "ShortContent" in types


def test_html_article_spider_schedule_cap_no_network() -> None:
    """Reserved slots cap scheduled Requests before responses complete."""
    sid = "ex_com"
    row: dict[str, Any] = {
        "source_id": sid,
        "_homepage_url": "https://example.com/",
        "_source_active": True,
    }
    spider = HtmlArticleSpider(sources=[row], max_articles_per_source=2, max_depth=2, summary=None)

    starts = list(spider.start_requests())
    assert len(starts) == 1
    assert isinstance(starts[0], Request)
    assert spider._reserved[sid] == 1
    assert spider._attempted[sid] == 0

    html = "<html><body>" + "".join(f'<a href="https://example.com/p{i}">x</a>' for i in range(50)) + "</body></html>"
    req = Request(url="https://example.com/")
    req.meta["source_id"] = sid
    req.meta["depth"] = 0
    req.meta["source_active"] = True
    resp = HtmlResponse(url=req.url, request=req, body=html.encode(), encoding="utf-8")

    out = list(spider.parse_page(resp))
    items = [x for x in out if isinstance(x, ArticleItem)]
    reqs = [x for x in out if isinstance(x, Request)]

    assert len(items) == 1
    assert spider._attempted[sid] == 1
    assert spider._reserved[sid] == 2
    assert len(reqs) == 1

    child_url = reqs[0].url
    child_html = "<html><body><a href=\"https://example.com/z\">z</a></body></html>"
    req2 = Request(url=child_url)
    req2.meta["source_id"] = sid
    req2.meta["depth"] = 1
    req2.meta["source_active"] = True
    resp2 = HtmlResponse(url=req2.url, request=req2, body=child_html.encode(), encoding="utf-8")

    out2 = list(spider.parse_page(resp2))
    items2 = [x for x in out2 if isinstance(x, ArticleItem)]
    reqs2 = [x for x in out2 if isinstance(x, Request)]

    assert len(items2) == 1
    assert spider._attempted[sid] == 2
    assert spider._reserved[sid] == 2
    assert len(reqs2) == 0


def test_html_article_spider_max_one_schedules_homepage_only() -> None:
    sid = "one_com"
    row = {"source_id": sid, "_homepage_url": "https://example.org/", "_source_active": True}
    spider = HtmlArticleSpider(sources=[row], max_articles_per_source=1, max_depth=2, summary=None)
    assert len(list(spider.start_requests())) == 1
    assert spider._reserved[sid] == 1

    html = "<html><body><a href=\"https://example.org/a\">a</a><a href=\"https://example.org/b\">b</a></body></html>"
    req = Request(url="https://example.org/")
    req.meta.update({"source_id": sid, "depth": 0, "source_active": True})
    resp = HtmlResponse(url=req.url, request=req, body=html.encode(), encoding="utf-8")
    out = list(spider.parse_page(resp))
    assert len([x for x in out if isinstance(x, Request)]) == 0
    assert spider._reserved[sid] == 1
