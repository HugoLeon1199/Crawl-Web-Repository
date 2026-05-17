"""Shared API adapter interface for TODAY GLOBAL INTELLIGENCE ENGINE v1."""

from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import httpx
from loguru import logger
from settings import CrawlRules


@dataclass
class ApiRecord:
    source_id: str
    api_name: str
    record_type: str
    title: str | None
    url: str
    published_at: str | None = None
    updated_at: str | None = None
    summary: str | None = None
    content: str | None = None
    language: str | None = None
    domain: str | None = None
    country: str | None = None
    authors: list[str] | None = None
    raw_metadata: dict[str, Any] = field(default_factory=dict)
    discovery_method: str = "api_first"


class ApiAdapter(ABC):
    name: str = ""
    requires_api_key: bool = False

    def collect_range(
        self,
        *,
        target_date_str: str | None,
        timezone_name: str,
        query: str,
        max_records: int | None,
        rules: CrawlRules,
        client: httpx.Client,
    ) -> list[ApiRecord]:
        return self.collect_today(
            target_date_str=target_date_str,
            timezone_name=timezone_name,
            query=query,
            max_records=max_records,
            rules=rules,
            client=client,
        )

    @abstractmethod
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
        ...


def http_get_with_retry(
    client: httpx.Client,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    max_attempts: int = 4,
    base_sleep: float = 1.25,
) -> httpx.Response:
    last: httpx.Response | None = None
    for attempt in range(max_attempts):
        try:
            r = client.get(url, params=params)
            last = r
            if r.status_code in (429, 503):
                time.sleep(base_sleep * (2**attempt))
                continue
            return r
        except httpx.HTTPError as exc:
            logger.warning("HTTP attempt {} failed {}: {}", attempt + 1, url, exc)
            time.sleep(base_sleep * (2**attempt))
    if last is not None:
        return last
    raise RuntimeError(f"no response for {url}")


def authors_to_json(authors: list[str] | None) -> str | None:
    if authors is None:
        return None
    return json.dumps(authors, ensure_ascii=False)
