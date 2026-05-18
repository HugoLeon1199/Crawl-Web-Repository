#!/usr/bin/env python3
"""Map config/sources_raw.txt -> source_ids and report DB coverage + URL totals."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import duckdb  # noqa: E402

from profiler.normalize import dedupe_sources, normalize_url  # noqa: E402
from run_profile import read_source_lines  # noqa: E402
from scrapy_engine.db_source_loader import load_sources_for_scrapy  # noqa: E402


def _utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


def main() -> int:
    _utf8_stdio()
    input_path = ROOT / "config" / "sources_raw.txt"
    db_path = ROOT / "data" / "db" / "web_intel.duckdb"

    raw_lines = read_source_lines(input_path)
    norms: list = []
    invalid = 0
    for u in raw_lines:
        try:
            norms.append(normalize_url(u))
        except Exception:
            invalid += 1
            continue
    uniq = dedupe_sources(norms)
    file_ids = sorted({n.source_id for n in uniq})

    print("")
    print("===== SOURCE FILE vs DB COVERAGE =====")
    print(f"- Input file: {input_path.name}")
    print(f"- Raw lines (non-empty, non-comment): {len(raw_lines)}")
    print(f"- Invalid / skipped URLs: {invalid}")
    print(f"- Unique source_id (dedupe by domain): {len(file_ids)}")
    print("")

    if not db_path.is_file():
        print("No DuckDB at", db_path)
        return 1

    placeholders = ",".join(["?" for _ in file_ids])
    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        prof_rows = conn.execute(
            f"SELECT source_id, best_strategy, status FROM source_profiles WHERE source_id IN ({placeholders})",
            file_ids,
        ).fetchall()
        prof_ids = {r[0] for r in prof_rows}

        d_disc = conn.execute(
            f"SELECT COUNT(*) FROM discovered_urls WHERE source_id IN ({placeholders})",
            file_ids,
        ).fetchone()[0]
        d_front = conn.execute(
            f"SELECT COUNT(*) FROM crawl_frontier WHERE source_id IN ({placeholders})",
            file_ids,
        ).fetchone()[0]
        d_union = conn.execute(
            f"""
            SELECT COUNT(*) FROM (
              SELECT DISTINCT url FROM discovered_urls WHERE source_id IN ({placeholders})
              UNION
              SELECT DISTINCT url FROM crawl_frontier WHERE source_id IN ({placeholders})
            ) u
            """,
            file_ids + file_ids,
        ).fetchone()[0]
        art_n = conn.execute(
            f"SELECT COUNT(*) FROM articles WHERE source_id IN ({placeholders})",
            file_ids,
        ).fetchone()[0]
    finally:
        conn.close()

    buckets = load_sources_for_scrapy(db_path, "all", 0)
    scrapy_ids = set()
    for rows in buckets.values():
        for row in rows:
            sid = row.get("source_id")
            if sid:
                scrapy_ids.add(sid)

    scrapy_in_file = sorted(scrapy_ids & set(file_ids))
    profiled_in_file = sorted(prof_ids)
    missing_profile = sorted(set(file_ids) - prof_ids)

    print(f"- source_id from file that have a row in source_profiles: {len(profiled_in_file)}")
    print(f"- source_id from file that are Scrapy-eligible (RSS/sitemap/HTML lane): {len(scrapy_in_file)}")
    print(f"- source_id from file with NO profile yet: {len(missing_profile)}")
    print("")
    print("----- URL volumes (only rows whose source_id is in the file set) -----")
    print(f"- Rows in discovered_urls: {d_disc}")
    print(f"- Rows in crawl_frontier: {d_front}")
    print(f"- DISTINCT url across discovered_urls UNION crawl_frontier: {d_union}")
    print(f"- Rows in articles (all time, same source_id filter): {art_n}")
    print("")
    print("(Scrapy-eligible source_ids from file:)")
    for sid in scrapy_in_file:
        print(f"  - {sid}")
    print("")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
