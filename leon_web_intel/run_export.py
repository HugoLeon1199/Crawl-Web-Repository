#!/usr/bin/env python3
"""Export DuckDB crawl artifacts and final crawl report."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from reporting.crawl_report import write_final_crawl_report  # noqa: E402
from storage.db import WebIntelDB  # noqa: E402


def main() -> int:
    db_path = ROOT / "data" / "db" / "web_intel.duckdb"
    out_dir = ROOT / "data" / "exports"
    out_dir.mkdir(parents=True, exist_ok=True)

    paths = {
        "articles_csv": out_dir / "articles.csv",
        "articles_parquet": out_dir / "articles.parquet",
        "crawl_errors_csv": out_dir / "crawl_errors.csv",
        "discovered_urls_csv": out_dir / "discovered_urls.csv",
        "crawl_frontier_csv": out_dir / "crawl_frontier.csv",
        "source_health_csv": out_dir / "source_health.csv",
        "final_report": out_dir / "final_crawl_report.md",
    }

    db = WebIntelDB(db_path)
    try:
        db.update_source_health_from_current_db()
        db.export_articles_csv(paths["articles_csv"])
        db.export_articles_parquet(paths["articles_parquet"])
        db.export_crawl_errors_csv(paths["crawl_errors_csv"])
        db.export_discovered_urls_csv(paths["discovered_urls_csv"])
        db.export_crawl_frontier_csv(paths["crawl_frontier_csv"])
        db.export_source_health_csv(paths["source_health_csv"])
        write_final_crawl_report(db, paths["final_report"])
    finally:
        db.close()

    print("===== EXPORTS WRITTEN =====")
    for path in paths.values():
        print(path.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
