"""Load SourceProfiler rows from DuckDB for Scrapy runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

import duckdb

StrategyKey = Literal["rss", "sitemap", "html", "all"]

ALLOWED_STRATEGIES = {
    "rss_then_article_extract",
    "sitemap_then_article_extract",
    "html_then_trafilatura",
    "playwright_fallback",
}

SKIP_STRATEGIES = {
    "api_first",
    "metadata_only",
    "manual_review",
}


def _parse_json_list(val: Any) -> list[str]:
    if val is None:
        return []
    if isinstance(val, list):
        return [str(x) for x in val if x]
    if isinstance(val, str):
        s = val.strip()
        if not s:
            return []
        try:
            data = json.loads(s)
            if isinstance(data, list):
                return [str(x) for x in data if x]
        except json.JSONDecodeError:
            return []
    return []


def _row_allowed_status(row: dict[str, Any]) -> bool:
    st = row.get("status") or ""
    return st in ("active", "active_candidate")


def _robots_allows_html(row: dict[str, Any]) -> bool:
    v = row.get("robots_can_fetch_homepage")
    if v is None:
        return True
    return bool(v)


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    rss_urls = _parse_json_list(row.get("rss_urls"))
    sitemap_urls = _parse_json_list(row.get("sitemap_urls"))
    homepage = row.get("homepage_url") or row.get("normalized_url") or ""
    out = dict(row)
    out["_rss_urls"] = rss_urls
    out["_sitemap_urls"] = sitemap_urls
    out["_homepage_url"] = str(homepage).strip()
    out["_source_active"] = True
    return out


def load_sources_for_scrapy(
    db_path: Path,
    strategy: StrategyKey,
    limit: int,
) -> dict[str, list[dict[str, Any]]]:
    """Return sources bucketed by Scrapy lane (rss / sitemap / html).

    Profiles must already have ``best_strategy`` from SourceProfiler.
    """
    if not db_path.is_file():
        return {"rss": [], "sitemap": [], "html": []}

    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        df = conn.execute(
            """
            SELECT * FROM source_profiles
            WHERE status IN ('active', 'active_candidate')
            ORDER BY source_id
            """
        ).fetchdf()
    finally:
        conn.close()

    rows = df.to_dict("records") if not df.empty else []
    rss_out: list[dict[str, Any]] = []
    sitemap_out: list[dict[str, Any]] = []
    html_out: list[dict[str, Any]] = []

    for row in rows:
        if not _row_allowed_status(row):
            continue
        strat = row.get("best_strategy") or ""
        if strat in SKIP_STRATEGIES or strat not in ALLOWED_STRATEGIES:
            continue
        norm = _normalize_row(row)
        if strat == "rss_then_article_extract" and norm["_rss_urls"]:
            rss_out.append(norm)
        elif strat == "sitemap_then_article_extract" and norm["_sitemap_urls"]:
            sitemap_out.append(norm)
        elif strat == "html_then_trafilatura":
            if not _robots_allows_html(row):
                continue
            if norm["_homepage_url"]:
                html_out.append(norm)
        elif strat == "playwright_fallback":
            if norm["_rss_urls"]:
                rss_out.append(norm)
            elif norm["_sitemap_urls"]:
                sitemap_out.append(norm)
            elif norm["_homepage_url"] and _robots_allows_html(row):
                html_out.append(norm)

    def clip(xs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if limit <= 0:
            return xs
        return xs[:limit]

    buckets = {
        "rss": clip(rss_out),
        "sitemap": clip(sitemap_out),
        "html": clip(html_out),
    }

    if strategy == "all":
        return buckets
    if strategy == "rss":
        return {"rss": buckets["rss"], "sitemap": [], "html": []}
    if strategy == "sitemap":
        return {"rss": [], "sitemap": buckets["sitemap"], "html": []}
    if strategy == "html":
        return {"rss": [], "sitemap": [], "html": buckets["html"]}
    raise ValueError(f"unknown strategy {strategy!r}")
