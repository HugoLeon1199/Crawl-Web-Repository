"""OpenAlex works API → ApiRecord."""

from __future__ import annotations

from typing import Any

import httpx

from collectors.api_adapters.base import ApiAdapter, ApiRecord, http_get_with_retry
from settings import CrawlRules
from utils.today_filter import resolve_calendar_date


def parse_openalex_works_response(data: dict[str, Any]) -> list[ApiRecord]:
    results = data.get("results")
    if not isinstance(results, list):
        return []
    out: list[ApiRecord] = []
    for w in results:
        if not isinstance(w, dict):
            continue
        wid = str(w.get("id") or "").strip()
        title = str(w.get("display_name") or "").strip() or None
        url = ""
        pl = w.get("primary_location")
        if isinstance(pl, dict):
            url = str(pl.get("landing_page_url") or pl.get("pdf_url") or "").strip()
        ids = w.get("ids")
        if isinstance(ids, dict):
            doi = ids.get("doi")
            if doi:
                url = str(doi)
        if not url and wid.startswith("http"):
            url = wid
        if not url:
            continue
        pub = w.get("publication_date") or w.get("publication_year")
        authors: list[str] = []
        authorships = w.get("authorships")
        if isinstance(authorships, list):
            for a in authorships:
                if isinstance(a, dict):
                    au = a.get("author")
                    if isinstance(au, dict) and au.get("display_name"):
                        authors.append(str(au["display_name"]))
        out.append(
            ApiRecord(
                source_id="api_openalex",
                api_name="openalex",
                record_type="scholarly_work",
                title=title,
                url=str(url),
                published_at=str(pub) if pub else None,
                summary=None,
                content=None,
                language=str(w.get("language") or "") or None,
                domain="openalex.org",
                country=None,
                authors=authors or None,
                raw_metadata={"openalex_id": wid, "work": w},
                discovery_method="api_openalex_works",
            )
        )
    return out


class OpenAlexAdapter(ApiAdapter):
    name = "openalex"
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
        unlimited = max_records is not None and max_records <= 0
        cap: int | None = None if unlimited else (max_records if max_records is not None else 500)
        flt = f"publication_date:{day}"
        if query and query not in ("*", ""):
            flt = f"{flt},title.search:{query}"
        url = "https://api.openalex.org/works"
        cursor = "*"
        out: list[ApiRecord] = []
        pages = 0
        while cursor and (cap is None or len(out) < cap) and pages < 80:
            pages += 1
            page_size = 200 if cap is None else min(200, max(1, cap - len(out)))
            params: dict[str, Any] = {"filter": flt, "per-page": page_size, "cursor": cursor}
            r = http_get_with_retry(client, url, params=params)
            if r.status_code >= 400:
                break
            data = r.json()
            batch = parse_openalex_works_response(data)
            out.extend(batch)
            meta = data.get("meta") if isinstance(data, dict) else None
            cursor = None
            if isinstance(meta, dict):
                cursor = meta.get("next_cursor")
            if not batch:
                break
        return out if cap is None else out[:cap]
