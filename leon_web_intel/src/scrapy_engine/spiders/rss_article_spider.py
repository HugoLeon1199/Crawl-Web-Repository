from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import feedparser
import scrapy

from scrapy_engine.items import ArticleItem
from utils.today_filter import (
    is_datetime_in_range,
    is_url_likely_today,
    parse_any_datetime,
    parse_datetime_from_feedparser_struct,
    resolve_calendar_date,
    target_date_range,
)


class RssArticleSpider(scrapy.Spider):
    """Production lane for ``rss_then_article_extract`` profiles."""

    name = "rss_article"

    def __init__(
        self,
        sources: list[dict[str, Any]] | None = None,
        max_articles_per_source: int = 5,
        summary: Any | None = None,
        crawl_strategy: str = "rss_then_article_extract",
        today_only: bool = False,
        target_date: str | None = None,
        timezone: str = "Europe/Amsterdam",
        max_urls_per_source: int = 1000,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.sources = sources or []
        self.max_articles_per_source = int(max_articles_per_source)
        self.summary = summary
        self.crawl_strategy = crawl_strategy
        self.today_only = bool(today_only)
        self.target_date_str = target_date
        self.timezone_str = str(timezone or "Europe/Amsterdam")
        self.max_urls_per_source = int(max_urls_per_source)
        self._reserved: dict[str, int] = {}

    def _sched(self, n: int = 1) -> None:
        if self.summary:
            with self.summary.lock:
                self.summary.requests_scheduled += n

    def _cap_for_source(self, sid: str) -> int:
        if self.today_only:
            return self.max_urls_per_source
        return self.max_articles_per_source

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

        if self.today_only:
            start_utc, end_utc = target_date_range(self.target_date_str, self.timezone_str)
            target_d = resolve_calendar_date(self.target_date_str, self.timezone_str)
            for entry in entries:
                if self._reserved.get(sid, 0) >= self.max_urls_per_source:
                    break
                link = entry.get("link") or entry.get("id")
                if not link:
                    continue
                link = str(link).strip()
                if not link.startswith("http"):
                    continue

                pub_dt = parse_datetime_from_feedparser_struct(entry.get("published_parsed"))
                if pub_dt is None:
                    pub_dt = parse_any_datetime(entry.get("published"))
                upd_dt = parse_datetime_from_feedparser_struct(entry.get("updated_parsed"))
                if upd_dt is None:
                    upd_dt = parse_any_datetime(entry.get("updated"))
                cand_dt = pub_dt or upd_dt
                cand_raw = None
                if cand_dt:
                    cand_raw = cand_dt.astimezone(timezone.utc).isoformat()
                elif entry.get("published"):
                    cand_raw = str(entry.get("published"))
                elif entry.get("updated"):
                    cand_raw = str(entry.get("updated"))

                include = False
                if cand_dt and is_datetime_in_range(cand_dt, start_utc, end_utc):
                    include = True
                elif cand_dt is None and is_url_likely_today(link, target_d):
                    include = True
                elif cand_dt and not is_datetime_in_range(cand_dt, start_utc, end_utc):
                    include = False
                elif is_url_likely_today(link, target_d):
                    include = True

                if not include:
                    continue

                self._reserved[sid] = self._reserved.get(sid, 0) + 1
                self._sched(1)
                yield scrapy.Request(
                    link,
                    callback=self.parse_article,
                    errback=self.errback,
                    meta={
                        "source_id": sid,
                        "source_active": active,
                        "candidate_published_at": cand_raw,
                    },
                    dont_filter=False,
                )
            return

        remaining = self._cap_for_source(sid) - self._reserved.get(sid, 0)
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
            pub_dt = parse_datetime_from_feedparser_struct(entry.get("published_parsed")) or parse_any_datetime(
                entry.get("published")
            )
            cand_raw = pub_dt.astimezone(timezone.utc).isoformat() if pub_dt else (
                str(entry.get("published")) if entry.get("published") else None
            )
            yield scrapy.Request(
                link,
                callback=self.parse_article,
                errback=self.errback,
                meta={
                    "source_id": sid,
                    "source_active": active,
                    "candidate_published_at": cand_raw,
                },
                dont_filter=False,
            )

    def parse_article(self, response: scrapy.http.Response) -> Any:
        sid = response.meta["source_id"]
        td = None
        if self.today_only:
            td = str(resolve_calendar_date(self.target_date_str, self.timezone_str))
        yield ArticleItem(
            source_id=sid,
            url=response.url,
            crawl_strategy_used=self.crawl_strategy,
            html_body=response.body,
            response_status=response.status,
            source_active=response.meta.get("source_active", True),
            candidate_published_at=response.meta.get("candidate_published_at"),
            discovery_source="rss",
            target_date=td,
            is_today_candidate=bool(self.today_only),
            discovered_at=datetime.now(timezone.utc).isoformat(),
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
