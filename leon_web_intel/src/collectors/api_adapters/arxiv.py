"""arXiv Atom API → ApiRecord."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

import httpx

from collectors.api_adapters.base import ApiAdapter, ApiRecord, http_get_with_retry
from settings import CrawlRules
from utils.today_filter import resolve_calendar_date


ARXIV_NS = {"atom": "http://www.w3.org/2005/Atom"}


def parse_arxiv_atom(xml_bytes: bytes) -> list[ApiRecord]:
    root = ET.fromstring(xml_bytes)
    out: list[ApiRecord] = []
    for entry in root.findall("atom:entry", ARXIV_NS):
        id_el = entry.find("atom:id", ARXIV_NS)
        title_el = entry.find("atom:title", ARXIV_NS)
        published_el = entry.find("atom:published", ARXIV_NS)
        updated_el = entry.find("atom:updated", ARXIV_NS)
        summary_el = entry.find("atom:summary", ARXIV_NS)
        url = (id_el.text or "").strip() if id_el is not None else ""
        if not url:
            continue
        title = (title_el.text or "").strip().replace("\n", " ") if title_el is not None else None
        summary = (summary_el.text or "").strip() if summary_el is not None else None
        authors: list[str] = []
        for au in entry.findall("atom:author", ARXIV_NS):
            nm = au.find("atom:name", ARXIV_NS)
            if nm is not None and nm.text:
                authors.append(nm.text.strip())
        pdf_link = None
        for link in entry.findall("atom:link", ARXIV_NS):
            if link.get("title") == "pdf":
                pdf_link = link.get("href")
        out.append(
            ApiRecord(
                source_id="api_arxiv",
                api_name="arxiv",
                record_type="preprint",
                title=title,
                url=url,
                published_at=published_el.text.strip() if published_el is not None and published_el.text else None,
                updated_at=updated_el.text.strip() if updated_el is not None and updated_el.text else None,
                summary=summary,
                content=None,
                language=None,
                domain="arxiv.org",
                country=None,
                authors=authors or None,
                raw_metadata={"pdf_url": pdf_link},
                discovery_method="api_arxiv_atom",
            )
        )
    return out


class ArxivAdapter(ApiAdapter):
    name = "arxiv"
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
        yyyymmdd = day.strftime("%Y%m%d")
        qbase = f"submittedDate:[{yyyymmdd}000000+TO+{yyyymmdd}235959]"
        if query and query not in ("*", ""):
            qbase = f"({qbase}) AND all:{query}"
        unlimited = max_records is None or max_records <= 0
        cap_eff = 2000 if unlimited else min(max_records, 2000)
        params = {"search_query": qbase, "start": 0, "max_results": cap_eff}
        r = http_get_with_retry(client, "http://export.arxiv.org/api/query", params=params)
        if r.status_code >= 400:
            return []
        parsed = parse_arxiv_atom(r.content)
        return parsed if unlimited else parsed[: max_records]
