"""Crossref works API → ApiRecord."""

from __future__ import annotations

from typing import Any

import httpx

from collectors.api_adapters.base import ApiAdapter, ApiRecord, http_get_with_retry
from settings import CrawlRules, merge_polite_mailto_param
from utils.today_filter import resolve_calendar_date


def parse_crossref_message_items(message: dict[str, Any]) -> list[ApiRecord]:
    items = message.get("items") or []
    if not isinstance(items, list):
        return []
    out: list[ApiRecord] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        title_list = it.get("title") or []
        title = title_list[0] if title_list else None
        doi = str(it.get("DOI") or "").strip()
        if not doi:
            continue
        url = str(it.get("URL") or f"https://doi.org/{doi}")
        issued = it.get("issued", {}).get("date-parts") if isinstance(it.get("issued"), dict) else None
        pub = None
        if isinstance(issued, list) and issued and isinstance(issued[0], list):
            parts = issued[0]
            pub = "-".join(str(p) for p in parts[:3])
        authors: list[str] = []
        for a in it.get("author") or []:
            if isinstance(a, dict):
                fam = a.get("family")
                giv = a.get("given")
                if fam:
                    authors.append(f"{giv + ' ' if giv else ''}{fam}".strip())
        out.append(
            ApiRecord(
                source_id="api_crossref",
                api_name="crossref",
                record_type="scholarly_work",
                title=str(title) if title else None,
                url=url,
                published_at=pub,
                summary=None,
                content=None,
                language=None,
                domain="doi.org",
                country=None,
                authors=authors or None,
                raw_metadata={"doi": doi, "publisher": it.get("publisher")},
                discovery_method="api_crossref_works",
            )
        )
    return out


class CrossrefAdapter(ApiAdapter):
    name = "crossref"
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
        flt = f"from-pub-date:{day},until-pub-date:{day}"
        url = "https://api.crossref.org/works"
        rows: list[ApiRecord] = []
        cursor = "*"
        unlimited = max_records is not None and max_records <= 0
        cap: int | None = None if unlimited else (max_records if max_records is not None else 200)
        pages = 0
        while cursor and (cap is None or len(rows) < cap) and pages < 80:
            pages += 1
            batch_rows = 100 if cap is None else min(100, max(1, cap - len(rows)))
            params: dict[str, Any] = {
                "filter": flt,
                "rows": batch_rows,
                "cursor": cursor,
            }
            if query and query not in ("*", ""):
                params["query.title"] = query
            params = merge_polite_mailto_param(rules, params)
            r = http_get_with_retry(client, url, params=params)
            if r.status_code >= 400:
                break
            body = r.json()
            msg = body.get("message") if isinstance(body, dict) else None
            if not isinstance(msg, dict):
                break
            batch = parse_crossref_message_items(msg)
            rows.extend(batch)
            cursor = msg.get("next-cursor")
            if not batch:
                break
        return rows if cap is None else rows[:cap]
