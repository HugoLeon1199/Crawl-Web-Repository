"""Load YAML configuration into typed models."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class JsDetectionConfig(BaseModel):
    min_text_length: int = 500
    script_count_threshold: int = 15
    js_keywords: list[str] = Field(default_factory=list)


class CrawlRules(BaseModel):
    user_agent: str = "LeonWebIntelBot/0.1 (+local research project)"
    request_timeout_seconds: float = 20.0
    max_retries: int = 2
    default_delay_seconds: float = 1.5
    concurrency: int = 20
    scrapy_concurrent_requests: int = 32
    scrapy_concurrent_requests_per_domain: int = 3
    profile_cache_days: int = 7
    http_cache_enabled: bool = True

    max_rss_candidates: int = 20
    max_sitemap_candidates: int = 10
    max_sitemaps_to_parse_in_profiler: int = 5
    max_urls_from_sitemap_in_profiler: int = 200

    min_extract_text_length: int = 300
    min_article_content_length: int = 300
    sample_max_articles_per_source: int = 5

    rss_candidate_paths: list[str] = Field(default_factory=list)
    sitemap_candidate_paths: list[str] = Field(default_factory=list)

    js_detection: JsDetectionConfig = Field(default_factory=JsDetectionConfig)
    paywall_keywords: list[str] = Field(default_factory=list)
    login_keywords: list[str] = Field(default_factory=list)
    captcha_keywords: list[str] = Field(default_factory=list)
    prefer_metadata_only_domains: list[str] = Field(default_factory=list)


class KnownAdapterEntry(BaseModel):
    domains: list[str]
    strategy: str = "api_first"
    adapter: str
    endpoint_hint: str | None = None


class KnownApiConfig(BaseModel):
    known_api_adapters: dict[str, KnownAdapterEntry]


def load_crawl_rules(path: Path) -> CrawlRules:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return CrawlRules.model_validate(data)


def load_known_api_config(path: Path) -> KnownApiConfig:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return KnownApiConfig.model_validate(data)


def flatten_known_domains(cfg: KnownApiConfig) -> dict[str, tuple[str, KnownAdapterEntry]]:
    """domain -> (adapter_key, entry)."""
    out: dict[str, tuple[str, KnownAdapterEntry]] = {}
    for key, entry in cfg.known_api_adapters.items():
        for d in entry.domains:
            canon = d.lower().lstrip(".")
            out[canon] = (key, entry)
    return out
