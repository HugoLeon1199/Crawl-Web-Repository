"""World Bank indicator API → macro ApiRecord (no strict \"today\")."""

from __future__ import annotations

from typing import Any

import httpx

from collectors.api_adapters.base import ApiAdapter, ApiRecord, http_get_with_retry
from settings import CrawlRules


def parse_world_bank_indicator_response(data: list[Any]) -> list[ApiRecord]:
    if len(data) < 2 or not isinstance(data[1], list):
        return []
    out: list[ApiRecord] = []
    for row in data[1]:
        if not isinstance(row, dict):
            continue
        cid = row.get("country")
        iso = ""
        if isinstance(cid, dict):
            iso = str(cid.get("id") or "")
        iso3 = str(row.get("countryiso3code") or iso)
        val = row.get("value")
        dt = str(row.get("date") or "")
        ind = row.get("indicator")
        ind_id = "indicator"
        ind_name = "indicator"
        if isinstance(ind, dict):
            ind_id = str(ind.get("id") or ind_id)
            ind_name = str(ind.get("value") or ind_id)
        api_url = f"https://api.worldbank.org/v2/country/{iso3}/indicator/{ind_id}?format=json&mrv=5"
        out.append(
            ApiRecord(
                source_id="api_world_bank",
                api_name="world_bank",
                record_type="macro_data",
                title=f"{ind_name} ({iso3})",
                url=api_url,
                published_at=dt,
                summary=str(val) if val is not None else None,
                content=None,
                language=None,
                domain="data.worldbank.org",
                country=iso3 or None,
                authors=None,
                raw_metadata={"indicator_id": ind_id, "date": dt, "value": val},
                discovery_method="api_world_bank_indicator",
            )
        )
    return out


class WorldBankAdapter(ApiAdapter):
    name = "world_bank"
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
        _ = target_date_str, timezone_name, query
        indicator = "NY.GDP.MKTP.CD"
        url = f"https://api.worldbank.org/v2/country/all/indicator/{indicator}"
        per = 500 if max_records is None or max_records <= 0 else min(max_records, 500)
        params = {"format": "json", "mrv": 1, "per_page": per}
        r = http_get_with_retry(client, url, params=params)
        if r.status_code >= 400:
            return []
        data = r.json()
        if not isinstance(data, list):
            return []
        rows = parse_world_bank_indicator_response(data)
        cap = None if max_records is None or max_records <= 0 else max_records
        return rows if cap is None else rows[:cap]
