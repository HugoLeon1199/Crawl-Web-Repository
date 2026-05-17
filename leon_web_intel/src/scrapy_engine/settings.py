"""Minimal Scrapy settings derived from ``config/crawl_rules.yaml``."""

from __future__ import annotations

from pathlib import Path

from scrapy.settings import Settings

from settings import CrawlRules


def build_scrapy_settings_dict(
    rules: CrawlRules,
    *,
    db_path: Path,
    crawl_rules_path: Path,
    raw_root: Path,
    summary: object,
) -> dict:
    """Project-style overrides; merged into Scrapy ``Settings``."""
    return {
        "BOT_NAME": "leon_web_intel_scrapy",
        "ROBOTSTXT_OBEY": True,
        # Asyncio reactor avoids some Windows/select-related hangs with the default reactor.
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "USER_AGENT": rules.user_agent,
        "DOWNLOAD_TIMEOUT": int(rules.request_timeout_seconds),
        "RETRY_TIMES": max(0, int(rules.max_retries)),
        "DOWNLOAD_DELAY": float(rules.default_delay_seconds),
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
        "CONCURRENT_REQUESTS": 8,
        "LOG_LEVEL": "INFO",
        "COOKIES_ENABLED": False,
        "TELNETCONSOLE_ENABLED": False,
        # Wall-clock cap so the CLI cannot hang forever on stuck downloads (CloseSpider is in EXTENSIONS_BASE).
        "CLOSESPIDER_TIMEOUT": 600,
        "ITEM_PIPELINES": {
            "scrapy_engine.pipelines.WebIntelArticlePipeline": 300,
        },
        "WEB_INTEL_DB_PATH": str(db_path.resolve()),
        "WEB_INTEL_CRAWL_RULES_PATH": str(crawl_rules_path.resolve()),
        "WEB_INTEL_RAW_ROOT": str(raw_root.resolve()),
        "WEB_INTEL_SUMMARY": summary,
        "WEB_INTEL_MIN_ARTICLE_LENGTH": rules.min_article_content_length,
    }


def build_scrapy_settings(
    rules: CrawlRules,
    *,
    db_path: Path,
    crawl_rules_path: Path,
    raw_root: Path,
    summary: object,
) -> Settings:
    s = Settings()
    s.setdict(build_scrapy_settings_dict(rules, db_path=db_path, crawl_rules_path=crawl_rules_path, raw_root=raw_root, summary=summary), priority="cmdline")
    return s
