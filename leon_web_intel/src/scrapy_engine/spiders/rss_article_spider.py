from __future__ import annotations

from typing import Any

import feedparser
import scrapy

from scrapy_engine.items import ArticleItem


class RssArticleSpider(scrapy.Spider):
    """Production lane for ``rss_then_article_extract`` profiles."""

    name = "rss_article"

    def __init__(
        self,
        sources: list[dict[str, Any]] | None = None,
        max_articles_per_source: int = 5,
        summary: Any | None = None,
        crawl_strategy: str = "rss_then_article_extract",
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.sources = sources or []
        self.max_articles_per_source = int(max_articles_per_source)
        self.summary = summary
        self.crawl_strategy = crawl_strategy
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
            for rss_url in row["_rss_urls"]:
                self._sched(1)
                yield scrapy.Request(
                    rss_url,
                    callback=self.parse_feed,
                    errback=self.errback,
                    meta={"source_id": sid, "source_active": active},
                    dont_filter=False,
                )

    def parse_feed(self, response: scrapy.http.Response) -> Any:
        sid = response.meta["source_id"]
        active = response.meta.get("source_active", True)
        parsed = feedparser.parse(response.body)
        entries = getattr(parsed, "entries", []) or []
        remaining = self.max_articles_per_source - self._reserved.get(sid, 0)
        for entry in entries:
            if remaining <= 0:
                break
            link = entry.get("link") or entry.get("id")
            if not link:
                continue
            link = str(link).strip()
            if not link.startswith("http"):
                continue
            self._reserved[sid] = self._reserved.get(sid, 0) + 1
            remaining -= 1
            self._sched(1)
            yield scrapy.Request(
                link,
                callback=self.parse_article,
                errback=self.errback,
                meta={"source_id": sid, "source_active": active},
                dont_filter=False,
            )

    def parse_article(self, response: scrapy.http.Response) -> Any:
        sid = response.meta["source_id"]
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
