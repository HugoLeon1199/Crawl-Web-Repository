"""NCBI E-utilities (PubMed) → ApiRecord."""

from __future__ import annotations

from typing import Any

import httpx

from collectors.api_adapters.base import ApiAdapter, ApiRecord, http_get_with_retry
from settings import CrawlRules
from utils.today_filter import resolve_calendar_date


def parse_pubmed_esummary(result: dict[str, Any]) -> list[ApiRecord]:
    out: list[ApiRecord] = []
    res = result.get("result") if isinstance(result, dict) else None
    if not isinstance(res, dict):
        return out
    uids = res.get("uids") or []
    if not isinstance(uids, list):
        return out
    for uid in uids:
        doc = res.get(str(uid))
        if not isinstance(doc, dict):
            continue
        title = str(doc.get("title") or "").strip() or None
        journal = doc.get("fulljournalname") or doc.get("source")
        pubdate = doc.get("pubdate") or doc.get("epubdate")
        authors_raw = doc.get("authors")
        authors: list[str] = []
        if isinstance(authors_raw, list):
            for a in authors_raw:
                if isinstance(a, dict) and a.get("name"):
                    authors.append(str(a["name"]))
        url = f"https://pubmed.ncbi.nlm.nih.gov/{uid}/"
        out.append(
            ApiRecord(
                source_id="api_pubmed",
                api_name="pubmed",
                record_type="literature",
                title=title,
                url=url,
                published_at=str(pubdate) if pubdate else None,
                summary=str(doc.get("sorttitle") or "") or None,
                content=None,
                language=None,
                domain="pubmed.ncbi.nlm.nih.gov",
                country=None,
                authors=authors or None,
                raw_metadata={"pmid": uid, "journal": journal},
                discovery_method="api_pubmed_esummary",
            )
        )
    return out


class PubMedAdapter(ApiAdapter):
    name = "pubmed"
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
        md = day.strftime("%Y/%m/%d")
        base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        term = f"{query}[Title/Abstract]" if query not in ("*", "") else ""
        if term:
            term = f"({term}) AND "
        term = f"{term}{md}[PDAT]"
        unlimited = max_records is not None and max_records <= 0
        cap = 500 if unlimited else min(max_records or 100, 500)
        es = http_get_with_retry(
            client,
            base + "esearch.fcgi",
            params={"db": "pubmed", "retmode": "json", "retmax": cap, "term": term},
        )
        if es.status_code >= 400:
            return []
        ids = (es.json().get("esearchresult") or {}).get("idlist") or []
        if not ids:
            return []
        sm = http_get_with_retry(
            client,
            base + "esummary.fcgi",
            params={"db": "pubmed", "retmode": "json", "id": ",".join(ids)},
        )
        if sm.status_code >= 400:
            return []
        return parse_pubmed_esummary(sm.json())
