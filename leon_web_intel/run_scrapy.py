#!/usr/bin/env python3
"""Production crawl layer (Scrapy) — runs after SourceProfiler wrote DuckDB profiles."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from scrapy_engine.runner import run_scrapy_engine  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description="Leon Web Intel — Scrapy crawl layer (post-profiler)")
    p.add_argument(
        "--strategy",
        choices=("rss", "sitemap", "html", "all"),
        default="all",
        help="Which profiler strategies to crawl (maps to rss/sitemap/html spiders)",
    )
    p.add_argument("--limit", type=int, default=50, help="Max sources per spider lane after filters")
    p.add_argument(
        "--max-articles-per-source",
        type=int,
        default=5,
        help="Cap article URL attempts per source (sample mode; ignored as primary cap when --today-only)",
    )
    p.add_argument(
        "--db",
        type=Path,
        default=ROOT / "data" / "db" / "web_intel.duckdb",
        help="Path to DuckDB written by run_profile.py",
    )
    p.add_argument("--run-id", default=None, help="Optional crawl_runs.run_id from run_pipeline.py")
    p.add_argument(
        "--close-spider-timeout",
        type=int,
        default=600,
        metavar="SEC",
        help="Scrapy CLOSESPIDER_TIMEOUT (wall-clock seconds for entire crawl)",
    )
    p.add_argument(
        "--today-only",
        action="store_true",
        help="Public-discovery mode: filter to target calendar day (RSS dates / sitemap lastmod / URL heuristics)",
    )
    p.add_argument(
        "--date",
        default="today",
        metavar="DATE",
        help='Calendar day as YYYY-MM-DD or the literal "today" (interpreted in --timezone)',
    )
    p.add_argument(
        "--timezone",
        default="Europe/Amsterdam",
        metavar="TZ",
        help="IANA timezone for interpreting --date and RSS/sitemap day bounds",
    )
    p.add_argument(
        "--max-urls-per-source",
        type=int,
        default=1000,
        metavar="N",
        help="Safety cap per source in today mode (RSS/sitemap); HTML lane uses min(300, N)",
    )
    args = p.parse_args()

    summary = run_scrapy_engine(
        root=ROOT,
        strategy=args.strategy,
        limit=args.limit,
        max_articles_per_source=args.max_articles_per_source,
        db_path=args.db,
        run_id=args.run_id,
        close_spider_timeout=args.close_spider_timeout,
        today_only=bool(args.today_only),
        target_date=args.date,
        timezone_name=args.timezone,
        max_urls_per_source=args.max_urls_per_source,
    )

    print("")
    print("===== SCRAPY RUN SUMMARY =====")
    print(f"Sources loaded (all lanes): {summary.sources_loaded}")
    print(f"HTTP requests scheduled (approx): {summary.requests_scheduled}")
    print(f"Pipeline items processed: {summary.pipeline_items}")
    print(f"Articles inserted: {summary.articles_inserted}")
    print(f"Crawl errors logged: {summary.errors_logged}")
    print(f"Duplicate content hashes skipped: {summary.duplicates_skipped}")
    if args.today_only:
        print(f"Today mode: date={args.date!r} timezone={args.timezone!r} max_urls_per_source={args.max_urls_per_source}")
    if args.run_id:
        print(f"Run ID: {args.run_id}")
    print(f"Database: {args.db.resolve()}")
    print("")


if __name__ == "__main__":
    main()
