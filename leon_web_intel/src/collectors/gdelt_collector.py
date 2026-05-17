"""GDELT DOC API 2 — ArtList retrieval with UTC time-window batching."""

from __future__ import annotations

import json
import time
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlparse

import httpx
from loguru import logger

GDELT_DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"
MAX_RECORDS = 250


def url_to_gdelt_source_id(url: str) -> str:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    safe = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in host)
    return f"gdelt_{safe.replace('.', '_')}"


def normalize_gdelt_query(q: str) -> str:
    s = (q or "").strip()
    if s in ("*", "", '""'):
        return "*"
    return s


def _fmt_gdelt_ts(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y%m%d%H%M%S")


def fetch_artlist_window(
    client: httpx.Client,
    *,
    query: str,
    window_start_utc: datetime,
    window_end_utc: datetime,
) -> list[dict[str, Any]]:
    """Single ArtList request for [start, end) in UTC."""
    params = {
        "query": normalize_gdelt_query(query),
        "mode": "ArtList",
        "format": "json",
        "maxrecords": str(MAX_RECORDS),
        "sort": "datedesc",
        "startdatetime": _fmt_gdelt_ts(window_start_utc),
        "enddatetime": _fmt_gdelt_ts(window_end_utc),
    }
    last: httpx.Response | None = None
    for attempt in range(5):
        try:
            r = client.get(GDELT_DOC_API, params=params, timeout=90.0)
        except (
            httpx.TimeoutException,
            httpx.ConnectError,
            httpx.NetworkError,
            OSError,
        ) as exc:
            sleep_s = min(45.0, 1.25 * (2**attempt))
            logger.warning(
                "GDELT transport error {} — retry in {:.1f}s (attempt {}/{})",
                exc,
                sleep_s,
                attempt + 1,
                5,
            )
            time.sleep(sleep_s)
            continue
        last = r
        if r.status_code in (429, 503):
            sleep_s = min(45.0, 1.25 * (2**attempt))
            logger.warning(
                "GDELT ArtList {} HTTP {} — retry in {:.1f}s (attempt {}/{})",
                params.get("startdatetime"),
                r.status_code,
                sleep_s,
                attempt + 1,
                5,
            )
            time.sleep(sleep_s)
            continue
        try:
            r.raise_for_status()
        except httpx.HTTPStatusError:
            sleep_s = min(30.0, 1.25 * (2**attempt))
            logger.warning(
                "GDELT ArtList HTTP {} — retry in {:.1f}s (attempt {}/{})",
                r.status_code,
                sleep_s,
                attempt + 1,
                5,
            )
            time.sleep(sleep_s)
            continue
        text = r.text.strip()
        if not text:
            return []
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            logger.warning("GDELT non-JSON response ({} chars): {!r}", len(text), text[:200])
            sleep_s = min(20.0, 1.25 * (2**attempt))
            time.sleep(sleep_s)
            continue
        arts = data.get("articles")
        if not isinstance(arts, list):
            sleep_s = min(15.0, 1.0 * (2**attempt))
            logger.warning("GDELT unexpected JSON shape — retry in {:.1f}s", sleep_s)
            time.sleep(sleep_s)
            continue
        return [a for a in arts if isinstance(a, dict)]
    if last is not None:
        logger.warning(
            "GDELT ArtList exhausted retries for window {} .. {} (last HTTP {})",
            params.get("startdatetime"),
            params.get("enddatetime"),
            getattr(last, "status_code", "?"),
        )
    return []


def _bisect_window(
    client: httpx.Client,
    *,
    query: str,
    start: datetime,
    end: datetime,
    seen_urls: set[str],
    out: list[dict[str, Any]],
    max_records_total: int | None,
) -> None:
    """Recursively subdivide if API returns a full page (possible truncation)."""
    if start >= end:
        return
    arts = fetch_artlist_window(client, query=query, window_start_utc=start, window_end_utc=end)
    for a in arts:
        u = str(a.get("url") or "").strip()
        if u and u not in seen_urls:
            seen_urls.add(u)
            out.append(a)
            if max_records_total is not None and len(out) >= max_records_total:
                return

    if len(arts) < MAX_RECORDS:
        return

    mid = start + (end - start) / 2
    if mid <= start or mid >= end:
        logger.warning(
            "GDELT window {} .. {} returned {} rows (possible truncation, cannot subdivide)",
            start,
            end,
            len(arts),
        )
        return
    _bisect_window(client, query=query, start=start, end=mid, seen_urls=seen_urls, out=out, max_records_total=max_records_total)
    if max_records_total is not None and len(out) >= max_records_total:
        return
    _bisect_window(client, query=query, start=mid, end=end, seen_urls=seen_urls, out=out, max_records_total=max_records_total)


def iter_gdelt_artlist_day(
    *,
    query: str,
    window_start_utc: datetime,
    window_end_utc: datetime,
    max_records_total: int | None,
    http_timeout: float = 90.0,
) -> Iterator[dict[str, Any]]:
    """
    Walk the UTC interval with 15-minute tiles, subdividing when a tile fills MAX_RECORDS.

    ``max_records_total`` None means no cap (beyond practical API limits).
    """
    seen: set[str] = set()
    collected: list[dict[str, Any]] = []

    step = timedelta(minutes=15)
    cur = window_start_utc
    with httpx.Client(
        headers={"User-Agent": "LeonWebIntelBot/0.1 (+research; gdelt-doc-api)"},
        follow_redirects=True,
        timeout=http_timeout,
    ) as client:
        while cur < window_end_utc:
            if max_records_total is not None and len(collected) >= max_records_total:
                break
            nxt = min(cur + step, window_end_utc)
            before = len(collected)
            _bisect_window(
                client,
                query=query,
                start=cur,
                end=nxt,
                seen_urls=seen,
                out=collected,
                max_records_total=max_records_total,
            )
            logger.info(
                "GDELT tile UTC {} .. {} — +{} articles (total unique {})",
                cur.isoformat(),
                nxt.isoformat(),
                len(collected) - before,
                len(collected),
            )
            cur = nxt

    yield from collected
