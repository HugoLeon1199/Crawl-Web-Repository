"""GDELT DOC 2.0 ArtList → ApiRecord."""

from __future__ import annotations

from typing import Any

import httpx

from collectors.api_adapters.base import ApiAdapter, ApiRecord
from collectors.gdelt_collector import iter_gdelt_artlist_day, normalize_gdelt_query, url_to_gdelt_source_id
from settings import CrawlRules
from utils.today_filter import target_date_range


def parse_gdelt_article_dict(art: dict[str, Any], *, api_name: str = "gdelt") -> ApiRecord | None:
    url = str(art.get("url") or "").strip()
    if not url.startswith("http"):
        return None
    title = str(art.get("title") or "").strip() or None
    seendate = str(art.get("seendate") or art.get("seenDate") or "").strip() or None
    domain = str(art.get("domain") or "").strip() or None
    lang = str(art.get("language") or art.get("lang") or "").strip() or None
    country = str(art.get("sourcecountry") or art.get("country") or "").strip() or None
    return ApiRecord(
        source_id=url_to_gdelt_source_id(url),
        api_name=api_name,
        record_type="news_article",
        title=title,
        url=url,
        published_at=seendate,
        summary=None,
        content=None,
        language=lang or None,
        domain=domain,
        country=country or None,
        authors=None,
        raw_metadata={"gdelt": art},
        discovery_method="api_gdelt_doc",
    )


class GdeltAdapter(ApiAdapter):
    name = "gdelt"
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
        _ = client  # iterator uses its own client
        start_utc, end_utc = target_date_range(target_date_str, timezone_name)
        out: list[ApiRecord] = []
        for art in iter_gdelt_artlist_day(
            query=normalize_gdelt_query(query),
            window_start_utc=start_utc,
            window_end_utc=end_utc,
            max_records_total=max_records,
            http_timeout=float(rules.request_timeout_seconds) + 30.0,
        ):
            rec = parse_gdelt_article_dict(art)
            if rec:
                out.append(rec)
        return out
