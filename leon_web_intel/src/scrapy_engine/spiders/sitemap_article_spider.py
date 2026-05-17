from __future__ import annotations

import gzip
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import urlparse

import scrapy

from scrapy_engine.items import ArticleItem


def _local(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _iter_locs(body: bytes) -> list[str]:
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        return []
    out: list[str] = []
    for el in root.iter():
        if _local(el.tag or "").lower() == "loc" and el.text:
            u = el.text.strip()
            if u:
                out.append(u)
    return out


def _maybe_decompress(response: scrapy.http.Response) -> bytes:
    body = response.body
    url = (response.url or "").lower()
    if url.endswith(".gz") or response.headers.get("Content-Type", b"").decode("latin-1", errors="ignore").find("gzip") >= 0:
        try:
            return gzip.decompress(body)
        except Exception:  # noqa: BLE001
            return body
    return body


class SitemapArticleSpider(scrapy.Spider):
    """Production lane for ``sitemap_then_article_extract`` profiles."""

    name = "sitemap_article"

    def __init__(
        self,
        sources: list[dict[str, Any]] | None = None,
        max_articles_per_source: int = 5,
        summary: Any | None = None,
        crawl_strategy: str = "sitemap_then_article_extract",
        max_sitemap_nested: int = 3,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.sources = sources or []
        self.max_articles_per_source = int(max_articles_per_source)
        self.summary = summary
        self.crawl_strategy = crawl_strategy
        self.max_sitemap_nested = int(max_sitemap_nested)
        self._reserved: dict[str, int] = {}

    def _sched(self, n: int = 1) -> None:
        if self.summary:
            with self.summary.lock:
                self.summary.requests_scheduled += n

    def start_requests(self) -> Any:
        for row in self.sources:
            sid = row["source_id"]
            self._reserved.setdefault(sid, 0)
            active = row.get("_source_active", True)
            domain_host = urlparse(row.get("_homepage_url") or "").netloc.lower()
            for sm_url in row["_sitemap_urls"]:
                self._sched(1)
                yield scrapy.Request(
                    sm_url,
                    callback=self.parse_sitemap,
                    errback=self.errback,
                    meta={
                        "source_id": sid,
                        "source_active": active,
                        "nested_depth": 0,
                        "domain_host": domain_host,
                    },
                    dont_filter=False,
                )

    def _looks_like_sitemap_url(self, url: str) -> bool:
        lower = url.lower()
        return lower.endswith(".xml") or lower.endswith(".xml.gz") or "sitemap" in lower

    def parse_sitemap(self, response: scrapy.http.Response) -> Any:
        sid = response.meta["source_id"]
        active = response.meta.get("source_active", True)
        nested = int(response.meta.get("nested_depth", 0))
        domain_host = (response.meta.get("domain_host") or "").lower()

        raw = _maybe_decompress(response)
        locs = _iter_locs(raw)
        remaining = self.max_articles_per_source - self._reserved.get(sid, 0)
        if remaining <= 0:
            return

        for loc in locs:
            if remaining <= 0:
                break
            parsed = urlparse(loc)
            child_host = parsed.netloc.lower()
            if domain_host and child_host and child_host != domain_host:
                continue

            if self._looks_like_sitemap_url(loc) and nested < self.max_sitemap_nested:
                self._sched(1)
                yield scrapy.Request(
                    loc,
                    callback=self.parse_sitemap,
                    errback=self.errback,
                    meta={
                        "source_id": sid,
                        "source_active": active,
                        "nested_depth": nested + 1,
                        "domain_host": domain_host or child_host,
                    },
                    dont_filter=False,
                )
                continue

            if not loc.startswith("http"):
                continue

            self._reserved[sid] = self._reserved.get(sid, 0) + 1
            remaining -= 1
            self._sched(1)
            yield scrapy.Request(
                loc,
                callback=self.parse_article,
                errback=self.errback,
                meta={"source_id": sid, "source_active": active},
                dont_filter=False,
            )

    def parse_article(self, response: scrapy.http.Response) -> Any:
        sid = response.meta["source_id"]
        ctype = (response.headers.get(b"Content-Type") or b"").decode("latin-1", errors="ignore").lower()
        if "xml" in ctype or response.url.lower().endswith(".xml"):
            # Navigated to a document page that is still XML — skip without crashing
            yield ArticleItem(
                source_id=sid,
                url=response.url,
                crawl_strategy_used=self.crawl_strategy,
                error_type="NonHtmlSkipped",
                error_message="xml content-type at article step",
                response_status=response.status,
                source_active=response.meta.get("source_active", True),
            )
            return

        yield ArticleItem(
            source_id=sid,
            url=response.url,
            crawl_strategy_used=self.crawl_strategy,
            html_body=response.body,
            response_status=response.status,
            source_active=response.meta.get("source_active", True),
        )

    def errback(self, failure: Any) -> Any:
        req = failure.request
        resp = getattr(failure.value, "response", None)
        status = resp.status if resp is not None else None
        yield ArticleItem(
            source_id=req.meta.get("source_id", ""),
            url=req.url,
            crawl_strategy_used=self.crawl_strategy,
            error_type="FetchError",
            error_message=repr(failure.value),
            response_status=status,
            source_active=req.meta.get("source_active", True),
        )
