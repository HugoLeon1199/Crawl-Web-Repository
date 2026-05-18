"""OpenAlex works API → ApiRecord."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import httpx
from loguru import logger

from collectors.api_adapters.base import ApiAdapter, ApiRecord, http_get_with_retry
from settings import CrawlRules, merge_polite_mailto_param
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
            params: dict[str, Any] = merge_polite_mailto_param(
                rules, {"filter": flt, "per-page": page_size, "cursor": cursor}
            )
            r = http_get_with_retry(client, url, params=params)
            if r.status_code >= 400:
                logger.warning("OpenAlex primary query HTTP {}", r.status_code)
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

        if not out and (not query or str(query).strip() in ("*", "")):
            try:
                d0 = date.fromisoformat(day)
            except ValueError:
                pass
            else:
                day_next = (d0 + timedelta(days=1)).isoformat()
                flt_fb = f"from_updated_date:{day},to_updated_date:{day_next}"
                logger.info(
                    "OpenAlex: no rows for publication_date={}, fetching works updated in [{} .. {})",
                    day,
                    day,
                    day_next,
                )
                cursor = "*"
                fb_cap = 50 if cap is None else min(50, cap)
                pages_fb = 0
                while cursor and len(out) < fb_cap and pages_fb < 15:
                    pages_fb += 1
                    page_size = min(25, max(1, fb_cap - len(out)))
                    params_fb: dict[str, Any] = merge_polite_mailto_param(
                        rules, {"filter": flt_fb, "per-page": page_size, "cursor": cursor}
                    )
                    r2 = http_get_with_retry(client, url, params=params_fb)
                    if r2.status_code >= 400:
                        logger.warning("OpenAlex fallback HTTP {}", r2.status_code)
                        break
                    data2 = r2.json()
                    batch2 = parse_openalex_works_response(data2)
                    for rec in batch2:
                        rec.raw_metadata = {
                            **rec.raw_metadata,
                            "openalex_collect_mode": "updated_date_fallback",
                        }
                    out.extend(batch2)
                    meta2 = data2.get("meta") if isinstance(data2, dict) else None
                    cursor = None
                    if isinstance(meta2, dict):
                        cursor = meta2.get("next_cursor")
                    if not batch2:
                        break

        return out if cap is None else out[:cap]
