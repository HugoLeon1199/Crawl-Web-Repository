#!/usr/bin/env python3
"""Export DuckDB crawl artifacts and final crawl report."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from reporting.crawl_report import write_final_crawl_report, write_today_crawl_report  # noqa: E402
from storage.db import WebIntelDB  # noqa: E402
from utils.today_filter import resolve_calendar_date, target_date_range  # noqa: E402
from reporting.gdelt_report import write_today_gdelt_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Leon Web Intel — export DuckDB artifacts")
    parser.add_argument(
        "--today-only",
        action="store_true",
        help="Write today_* exports filtered to target calendar day in timezone",
    )
    parser.add_argument(
        "--date",
        default="today",
        metavar="DATE",
        help='YYYY-MM-DD or "today"',
    )
    parser.add_argument(
        "--timezone",
        default="Europe/Amsterdam",
        metavar="TZ",
        help="IANA timezone used with --date",
    )
    args = parser.parse_args()

    db_path = ROOT / "data" / "db" / "web_intel.duckdb"
    out_dir = ROOT / "data" / "exports"
    out_dir.mkdir(parents=True, exist_ok=True)

    paths = {
        "articles_csv": out_dir / "articles.csv",
        "articles_metadata_csv": out_dir / "articles_metadata.csv",
        "articles_parquet": out_dir / "articles.parquet",
        "crawl_errors_csv": out_dir / "crawl_errors.csv",
        "discovered_urls_csv": out_dir / "discovered_urls.csv",
        "crawl_frontier_csv": out_dir / "crawl_frontier.csv",
        "source_health_csv": out_dir / "source_health.csv",
        "final_report": out_dir / "final_crawl_report.md",
    }

    today_paths = {
        "articles_csv": out_dir / "today_articles.csv",
        "articles_metadata_csv": out_dir / "today_articles_metadata.csv",
        "articles_parquet": out_dir / "today_articles.parquet",
        "crawl_errors_csv": out_dir / "today_crawl_errors.csv",
        "crawl_frontier_csv": out_dir / "today_crawl_frontier.csv",
        "source_health_csv": out_dir / "today_source_health.csv",
        "final_report": out_dir / "today_final_report.md",
        "gdelt_metadata_csv": out_dir / "today_gdelt_metadata.csv",
        "gdelt_report_md": out_dir / "today_gdelt_report.md",
    }

    meta_path = out_dir / "today_run_meta.json"

    db = WebIntelDB(db_path)
    try:
        db.update_source_health_from_current_db()
        if args.today_only:
            db.export_today_articles_csv(today_paths["articles_csv"], target_date_str=args.date, timezone_name=args.timezone)
            db.export_today_articles_metadata_csv(
                today_paths["articles_metadata_csv"], target_date_str=args.date, timezone_name=args.timezone
            )
            db.export_today_articles_parquet(
                today_paths["articles_parquet"], target_date_str=args.date, timezone_name=args.timezone
            )
            db.export_today_errors_csv(today_paths["crawl_errors_csv"], target_date_str=args.date, timezone_name=args.timezone)
            db.export_today_frontier_csv(today_paths["crawl_frontier_csv"], target_date_str=args.date, timezone_name=args.timezone)
            db.export_today_source_health_csv(
                today_paths["source_health_csv"], target_date_str=args.date, timezone_name=args.timezone
            )
            write_today_crawl_report(
                db,
                today_paths["final_report"],
                target_date=args.date,
                timezone_name=args.timezone,
                run_meta_path=meta_path,
            )

            target_cal = str(resolve_calendar_date(args.date, args.timezone))
            db.export_gdelt_doc_hits_csv(
                today_paths["gdelt_metadata_csv"], target_calendar_date=target_cal, timezone_name=args.timezone
            )
            st_u, en_u = target_date_range(args.date, args.timezone)
            hits_n = db.count_gdelt_doc_hits(target_calendar_date=target_cal, timezone_name=args.timezone)
            gx = db.gdelt_day_extract_stats(target_calendar_date=target_cal, timezone_name=args.timezone)
            write_today_gdelt_report(
                today_paths["gdelt_report_md"],
                target_calendar_date=target_cal,
                timezone_name=args.timezone,
                utc_window=(st_u, en_u),
                query="(see gdelt run / api_query column in CSV)",
                total_hits=hits_n,
                extracted_ok=int(gx["extracted_linked"]),
                extract_errors=int(gx["extract_errors_logged"]),
                argv=["run_export.py", "--today-only", "--date", args.date, "--timezone", args.timezone],
            )

        db.export_articles_csv(paths["articles_csv"])
        db.export_articles_metadata_csv(paths["articles_metadata_csv"])
        db.export_articles_parquet(paths["articles_parquet"])
        db.export_crawl_errors_csv(paths["crawl_errors_csv"])
        db.export_discovered_urls_csv(paths["discovered_urls_csv"])
        db.export_crawl_frontier_csv(paths["crawl_frontier_csv"])
        db.export_source_health_csv(paths["source_health_csv"])
        write_final_crawl_report(db, paths["final_report"])
    finally:
        db.close()

    print("===== EXPORTS WRITTEN =====")
    if args.today_only:
        for path in today_paths.values():
            print(path.resolve())
        print(meta_path.resolve())
    for path in paths.values():
        print(path.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
