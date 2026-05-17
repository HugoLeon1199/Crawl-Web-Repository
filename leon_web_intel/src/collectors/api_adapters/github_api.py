"""GitHub REST search → ApiRecord."""

from __future__ import annotations

from typing import Any

import httpx
from loguru import logger

from collectors.api_adapters.base import ApiAdapter, ApiRecord, http_get_with_retry
from settings import CrawlRules
from utils.today_filter import resolve_calendar_date


def parse_github_search_repositories(data: dict[str, Any]) -> list[ApiRecord]:
    items = data.get("items") or []
    if not isinstance(items, list):
        return []
    out: list[ApiRecord] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        html_url = str(it.get("html_url") or "").strip()
        if not html_url:
            continue
        out.append(
            ApiRecord(
                source_id="api_github",
                api_name="github",
                record_type="code_host",
                title=str(it.get("full_name") or it.get("name") or ""),
                url=html_url,
                published_at=None,
                updated_at=str(it.get("updated_at") or "") or None,
                summary=str(it.get("description") or "") or None,
                content=None,
                language=str(it.get("language") or "") or None,
                domain="github.com",
                country=None,
                authors=[str(it.get("owner", {}).get("login") or "")] if isinstance(it.get("owner"), dict) else None,
                raw_metadata={
                    "stars": it.get("stargazers_count"),
                    "pushed_at": it.get("pushed_at"),
                },
                discovery_method="api_github_search",
            )
        )
    return out


class GitHubApiAdapter(ApiAdapter):
    name = "github"
    requires_api_key = False

    def collect_today(
        self,
        *,
        target_date_str: str | None,
        timezone_name: str,
        query: str,
        max_records: int | None,
        rules: CrawlRules,
        client: httpx.Client,
    ) -> list[ApiRecord]:
        day = resolve_calendar_date(target_date_str, timezone_name)
        ds = day.isoformat()
        q = f"pushed:{ds}"
        if query and query not in ("*", ""):
            q = f"{query} pushed:{ds}"
        url = "https://api.github.com/search/repositories"
        per = 100 if max_records is None or max_records <= 0 else min(max_records, 100)
        params = {"q": q, "per_page": per, "sort": "updated"}
        r = http_get_with_retry(client, url, params=params)
        if r.status_code == 403:
            logger.warning(
                "GitHub search HTTP 403 (rate limit or abuse?) — set GITHUB_TOKEN or retry later; empty batch"
            )
            return []
        if r.status_code >= 400:
            logger.warning("GitHub search HTTP {} — empty batch", r.status_code)
            return []
        return parse_github_search_repositories(r.json())
