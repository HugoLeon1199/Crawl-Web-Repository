#!/usr/bin/env python3
"""Count articles per source_id in a rolling window by extracted_at (UTC)."""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Articles per source in last N days (extracted_at, UTC)"
    )
    p.add_argument("--days", type=int, default=7, metavar="N", help="Rolling window length")
    p.add_argument("--db", type=Path, default=ROOT / "data" / "db" / "web_intel.duckdb")
    p.add_argument("--csv-out", type=Path, default=None)
    args = p.parse_args(argv)

    if not args.db.is_file():
        print(f"No database file: {args.db}", file=sys.stderr)
        return 1

    cutoff = datetime.now(timezone.utc) - timedelta(days=max(1, args.days))

    try:
        import duckdb
    except ImportError as exc:
        print(exc, file=sys.stderr)
        return 1

    try:
        con = duckdb.connect(str(args.db), read_only=True)
    except Exception as exc:
        print(f"Cannot open DuckDB (another job may hold an exclusive lock): {exc}", file=sys.stderr)
        return 2

    try:
        rows = con.execute(
            """
            SELECT source_id, COUNT(*) AS articles_n
            FROM articles
            WHERE extracted_at IS NOT NULL AND extracted_at >= ?
            GROUP BY source_id
            ORDER BY articles_n DESC, source_id
            """,
            [cutoff],
        ).fetchall()
        total = sum(r[1] for r in rows)
        print("")
        print(f"Window: extracted_at >= {cutoff.isoformat()} (UTC)")
        print(f"Rolling days: {args.days}")
        print(f"Sources with >= 1 article: {len(rows)}")
        print(f"Total articles in window: {total}")
        print("")
        print("source_id | articles")
        print("--- | ---:")
        for sid, n in rows:
            print(f"{sid} | {n}")
        print("")

        if args.csv_out is not None:
            args.csv_out.parent.mkdir(parents=True, exist_ok=True)
            with args.csv_out.open("w", encoding="utf-8", newline="") as fh:
                w = csv.writer(fh)
                w.writerow(["source_id", "articles_n"])
                w.writerows(rows)
            print(f"CSV: {args.csv_out.resolve()}")
        return 0
    finally:
        con.close()


if __name__ == "__main__":
    raise SystemExit(main())
