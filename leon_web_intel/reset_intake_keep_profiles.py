#!/usr/bin/env python3
"""Clear crawl/API/GDELT intake tables and stale exports; keep source_profiles (classified sources)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPORTS = ROOT / "data" / "exports"
DEFAULT_DB = ROOT / "data" / "db" / "web_intel.duckdb"

# Keep classifier snapshot exports (regenerated only when profiling runs).
KEEP_NAMES = frozenset({"source_profiles.csv", "source_profiles.parquet"})


def _utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


def wipe_database(con, *, dry_run: bool) -> None:
    tables = (
        "articles",
        "discovered_urls",
        "crawl_errors",
        "crawl_frontier",
        "crawl_runs",
        "source_health",
        "api_records",
        "gdelt_doc_hits",
    )
    for t in tables:
        sql = f"DELETE FROM {t}"
        if dry_run:
            print(f"[dry-run] {sql}")
        else:
            con.execute(sql)
            print(f"Cleared {t}")


def wipe_exports(*, dry_run: bool) -> None:
    if not EXPORTS.is_dir():
        return
    removed = 0
    for p in sorted(EXPORTS.iterdir()):
        if not p.is_file():
            continue
        if p.name in KEEP_NAMES:
            continue
        if p.name.startswith("today_") or p.name.startswith("articles_today"):
            pass
        elif p.name in {
            "articles.csv",
            "articles_metadata.csv",
            "articles.parquet",
            "crawl_errors.csv",
            "crawl_frontier.csv",
            "discovered_urls.csv",
            "source_health.csv",
            "final_crawl_report.md",
            "profile_summary.md",
            "source_intake_today.md",
            "articles_per_profiled_source_last_week.md",
            "today_run_meta.json",
            "_articles_today_detail_tmp.csv",
        }:
            pass
        else:
            continue
        if dry_run:
            print(f"[dry-run] unlink {p}")
        else:
            p.unlink()
            removed += 1
    if not dry_run:
        print(f"Removed {removed} export file(s) under {EXPORTS} (kept {sorted(KEEP_NAMES)})")


def main() -> int:
    _utf8_stdio()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    try:
        import duckdb
    except ImportError as exc:
        print(exc, file=sys.stderr)
        return 1

    if not args.db.is_file():
        print(f"No database at {args.db}", file=sys.stderr)
        return 2

    wipe_exports(dry_run=args.dry_run)

    if args.dry_run:
        print(f"[dry-run] would open {args.db} and DELETE FROM intake tables (not source_profiles)")
        return 0

    con = duckdb.connect(str(args.db))
    try:
        wipe_database(con, dry_run=False)
        con.execute("CHECKPOINT")
    finally:
        con.close()

    print("Reset complete; source_profiles unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
