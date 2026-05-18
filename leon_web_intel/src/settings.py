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
    # SEC fair access + OpenAlex/Crossref polite pool + NCBI etiquette — use env WEB_INTEL_CONTACT_EMAIL if unset.
    contact_email: str | None = None
    contact_display_name: str = "LeonWebIntel"
    ncbi_tool_name: str = "leon_web_intel"
    request_timeout_seconds: float = 20.0
    max_retries: int = 2
    default_delay_seconds: float = 1.5
    concurrency: int = 20
    scrapy_concurrent_requests: int = 32
    scrapy_concurrent_requests_per_domain: int = 3
    profile_cache_days: int = 7
    http_cache_enabled: bool = True

    max_rss_candidates: int = 20
    # Hard cap on RSS URL probe GETs during profiling (prevents multi-hour stalls).
    profiler_max_rss_http_attempts: int = 40
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

    # Max-collection: keep trafilatura output even if HTML shell matches paywall/login keywords (not captcha).
    keep_extract_despite_access_signal_if_meets_min_length: bool = False
    # Today-mode: accept articles without a parsed date when URL/day heuristics are inconclusive (broader intake).
    today_allow_undated_uncertain_urls: bool = False


class KnownAdapterEntry(BaseModel):
    domains: list[str]
    strategy: str = "api_first"
    adapter: str
    endpoint_hint: str | None = None


class KnownApiConfig(BaseModel):
    known_api_adapters: dict[str, KnownAdapterEntry]


def load_crawl_rules(path: Path) -> CrawlRules:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    local_path = path.with_name("crawl_rules.local.yaml")
    if local_path.is_file():
        local = yaml.safe_load(local_path.read_text(encoding="utf-8")) or {}
        if isinstance(local, dict):
            data = {**data, **local}
    return CrawlRules.model_validate(data)


def resolve_contact_email(rules: CrawlRules) -> str | None:
    """Prefer WEB_INTEL_CONTACT_EMAIL, then OPENALEX_CONTACT_EMAIL, then YAML contact_email."""
    import os

    for key in ("WEB_INTEL_CONTACT_EMAIL", "OPENALEX_CONTACT_EMAIL"):
        v = (os.getenv(key) or "").strip()
        if v:
            return v
    if rules.contact_email is None:
        return None
    s = str(rules.contact_email).strip()
    return s or None


def build_api_user_agent(rules: CrawlRules) -> str:
    """SEC: 'ScriptName contact@example.org'; OpenAlex/Crossref polite pool also expect identifiable UA."""
    email = resolve_contact_email(rules)
    if email:
        name = (rules.contact_display_name or "LeonWebIntel").strip()
        return f"{name} {email}"
    return rules.user_agent


def merge_polite_mailto_param(rules: CrawlRules, params: dict[str, Any]) -> dict[str, Any]:
    """OpenAlex & Crossref recommend a mailto= query param for the polite pool."""
    email = resolve_contact_email(rules)
    if not email:
        return dict(params)
    out = dict(params)
    out.setdefault("mailto", email)
    return out


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
