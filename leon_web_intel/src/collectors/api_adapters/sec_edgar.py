"""SEC EDGAR submissions JSON → ApiRecord."""

from __future__ import annotations

from typing import Any

import httpx
from loguru import logger

from collectors.api_adapters.base import ApiAdapter, ApiRecord, http_get_with_retry
from settings import CrawlRules, resolve_contact_email
from utils.today_filter import resolve_calendar_date


def parse_sec_submissions_json(data: dict[str, Any], *, target_filing_date: str) -> list[ApiRecord]:
    meta_name = str(data.get("name") or "")
    cik = str(data.get("cik") or "").zfill(10)
    recent = (data.get("filings") or {}).get("recent") or {}
    forms = recent.get("form") or []
    dates = recent.get("filingDate") or []
    accs = recent.get("accessionNumber") or []
    primary_docs = recent.get("primaryDocument") or []
    out: list[ApiRecord] = []
    n = min(len(forms), len(dates), len(accs))
    for i in range(n):
        fd = str(dates[i])
        if fd != target_filing_date:
            continue
        acc_fmt = str(accs[i])
        acc_flat = acc_fmt.replace("-", "")
        form = str(forms[i])
        doc = primary_docs[i] if i < len(primary_docs) else ""
        cik_int = int(cik)
        landing = (
            f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_flat}/{doc}"
            if doc
            else f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type={form}"
        )
        out.append(
            ApiRecord(
                source_id=f"api_sec_{cik}",
                api_name="sec",
                record_type="sec_filing",
                title=f"{meta_name} — {form}",
                url=landing,
                published_at=fd,
                summary=None,
                content=None,
                language=None,
                domain="sec.gov",
                country="US",
                authors=None,
                raw_metadata={"cik": cik, "accession": acc_fmt, "form": form},
                discovery_method="api_sec_submissions",
            )
        )
    return out


class SecEdgarAdapter(ApiAdapter):
    name = "sec"
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
        cik = (query.strip() if query and query not in ("*", "") and query.isdigit() else "320193").zfill(10)
        if not resolve_contact_email(rules):
            logger.warning(
                "SEC EDGAR fair access requires User-Agent identifying you (email). "
                "Set contact_email in crawl_rules.yaml or WEB_INTEL_CONTACT_EMAIL — otherwise HTTP 403 is likely."
            )
        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        r = http_get_with_retry(client, url)
        if r.status_code >= 400:
            return []
        data = r.json()
        rows = parse_sec_submissions_json(data, target_filing_date=day)
        cap = max_records if max_records is not None else 500
        return rows[:cap]
