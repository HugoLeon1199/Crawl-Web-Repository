"""Semantic Scholar Graph API → ApiRecord."""

from __future__ import annotations

from typing import Any

import httpx
from loguru import logger

from collectors.api_adapters.base import ApiAdapter, ApiRecord, http_get_with_retry
from settings import CrawlRules
from utils.today_filter import resolve_calendar_date


def parse_semantic_scholar_search(data: dict[str, Any]) -> list[ApiRecord]:
    raw = data.get("data") or []
    if not isinstance(raw, list):
        return []
    out: list[ApiRecord] = []
    for p in raw:
        if not isinstance(p, dict):
            continue
        pid = str(p.get("paperId") or "").strip()
        if not pid:
            continue
        title = str(p.get("title") or "").strip() or None
        url = str(p.get("url") or f"https://www.semanticscholar.org/paper/{pid}")
        pub = p.get("publicationDate") or p.get("year")
        abstract = str(p.get("abstract") or "").strip() or None
        authors: list[str] = []
        for a in p.get("authors") or []:
            if isinstance(a, dict) and a.get("name"):
                authors.append(str(a["name"]))
        cites = p.get("citationCount")
        out.append(
            ApiRecord(
                source_id="api_semantic_scholar",
                api_name="semantic_scholar",
                record_type="scholarly_work",
                title=title,
                url=url,
                published_at=str(pub) if pub else None,
                summary=abstract[:500] if abstract else None,
                content=abstract,
                language=None,
                domain="semanticscholar.org",
                country=None,
                authors=authors or None,
                raw_metadata={"paperId": pid, "citations": cites},
                discovery_method="api_semantic_scholar_search",
            )
        )
    return out


class SemanticScholarAdapter(ApiAdapter):
    name = "semantic_scholar"
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
        day = str(resolve_calendar_date(target_date_str, timezone_name))
        q = query if query not in ("*", "") else "a"
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        lim = 100 if max_records is None or max_records <= 0 else min(max_records, 100)
        params: dict[str, Any] = {
            "query": q,
            "limit": lim,
            "fields": "title,authors,year,abstract,url,publicationDate,citationCount,paperId",
        }
        r = http_get_with_retry(client, url, params=params)
        if r.status_code == 429:
            logger.warning("Semantic Scholar search rate limited (429); skipping adapter batch")
            return []
        if r.status_code >= 400:
            logger.warning("Semantic Scholar search HTTP {} — empty batch", r.status_code)
            return []
        data = r.json()
        rows = parse_semantic_scholar_search(data)
        cap = None if max_records is None or max_records <= 0 else max_records
        matched = [r for r in rows if r.published_at == day or (r.published_at or "").startswith(day)]
        picked = matched or rows
        return picked if cap is None else picked[:cap]
