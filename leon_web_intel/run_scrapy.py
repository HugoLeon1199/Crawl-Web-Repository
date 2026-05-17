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
        help="Cap article URL attempts per source within this lane",
    )
    p.add_argument(
        "--db",
        type=Path,
        default=ROOT / "data" / "db" / "web_intel.duckdb",
        help="Path to DuckDB written by run_profile.py",
    )
    args = p.parse_args()

    summary = run_scrapy_engine(
        root=ROOT,
        strategy=args.strategy,
        limit=args.limit,
        max_articles_per_source=args.max_articles_per_source,
        db_path=args.db,
    )

    print("")
    print("===== SCRAPY RUN SUMMARY =====")
    print(f"Sources loaded (all lanes): {summary.sources_loaded}")
    print(f"HTTP requests scheduled (approx): {summary.requests_scheduled}")
    print(f"Pipeline items processed: {summary.pipeline_items}")
    print(f"Articles inserted: {summary.articles_inserted}")
    print(f"Crawl errors logged: {summary.errors_logged}")
    print(f"Duplicate content hashes skipped: {summary.duplicates_skipped}")
    print(f"Database: {args.db.resolve()}")
    print("")


if __name__ == "__main__":
    main()
