#!/usr/bin/env python3
"""Print intake stats: raw source lines vs profiled vs Scrapy-eligible vs today's parsed remainder."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from profiler.normalize import dedupe_sources, normalize_url  # noqa: E402
from run_profile import read_source_lines  # noqa: E402
from scrapy_engine.db_source_loader import load_sources_for_scrapy  # noqa: E402
from storage.db import WebIntelDB  # noqa: E402


def count_raw_nonempty_lines(path: Path) -> int:
    if not path.is_file():
        return 0
    return len(read_source_lines(path))


def deduped_source_count(path: Path) -> int:
    urls = read_source_lines(path)
    norms = []
    for u in urls:
        try:
            norms.append(normalize_url(u))
        except Exception:
            continue
    return len(dedupe_sources(norms))


def _utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Source intake snapshot (today window)")
    p.add_argument("--input", type=Path, default=ROOT / "config" / "sources_raw.txt")
    p.add_argument("--date", default="today")
    p.add_argument("--timezone", default="Europe/Amsterdam", metavar="TZ")
    p.add_argument("--db", type=Path, default=ROOT / "data" / "db" / "web_intel.duckdb")
    p.add_argument("--csv-out", type=Path, default=None, help="Optional per-source CSV path")
    args = p.parse_args(argv)
    _utf8_stdio()

    raw_lines = count_raw_nonempty_lines(args.input)
    dedup_n = deduped_source_count(args.input)

    db_path = args.db
    scrapy_eligible = 0
    if db_path.is_file():
        buckets = load_sources_for_scrapy(db_path, "all", 0)
        scrapy_eligible = len(buckets["rss"]) + len(buckets["sitemap"]) + len(buckets["html"])

    db = WebIntelDB(db_path)
    try:
        snap = db.source_intake_snapshot(target_date_str=args.date, timezone_name=args.timezone)
    finally:
        db.close()

    tot = snap["totals"]
    prof_n = snap["profiled_sources_total"]
    src_with_article = sum(1 for r in snap["rows"] if r["articles_extracted_today"] > 0)

    print("")
    print("===== BÁO CÁO NGUỒN (SOURCE INTAKE) =====")
    print(f"- File nguồn (dòng URL không trống / không comment): {raw_lines}")
    print(f"- Số domain/source sau dedupe (profiler target): {dedup_n}")
    print(f"- Đã có profile trong DuckDB: {prof_n}")
    print(f"- Nguồn đủ điều kiện vào Scrapy (RSS/sitemap/HTML, không api_only…): {scrapy_eligible}")
    print("")
    print(f"--- Cửa sổ NGÀY {snap['target_calendar_date']} ({args.timezone}) ---")
    print(f"UTC: {snap['window_start_utc']} → {snap['window_end_utc']}")
    print(f"- URL discovered (ghi nhận hôm nay trong cửa sổ): {tot['discovered_today']}")
    print(f"- Bài article extract được (extracted_at hôm nay): {tot['articles_extracted_today']}")
    print(f"- Ước lượng còn lại (discovered − article, ≥0): {tot['remaining_estimate']}")
    print(f"- Frontier pending/crawling (chạm cửa sổ): {tot['frontier_pending_today']}")
    print(f"- Frontier failed (chạm cửa sổ): {tot['frontier_failed_today']}")
    print(f"- Số source_id có ít nhất 1 bài hôm nay: {src_with_article}")
    print("")
    print("source_id | discovered_hôm_nay | article_hôm_nay | còn_lại_ước_lượng | frontier_pending | frontier_failed")
    print("--- | ---: | ---: | ---: | ---: | ---:")
    for r in snap["rows"]:
        print(
            f"{r['source_id']} | {r['discovered_today']} | {r['articles_extracted_today']} | "
            f"{r['remaining_estimate']} | {r['frontier_pending_today']} | {r['frontier_failed_today']}"
        )
    print("")

    md_path = ROOT / "data" / "exports" / "source_intake_today.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Source intake — today window",
        "",
        f"- Raw lines in `{args.input.name}`: **{raw_lines}**",
        f"- Deduped profiler targets: **{dedup_n}**",
        f"- Profiled in DuckDB: **{prof_n}**",
        f"- Scrapy-eligible sources: **{scrapy_eligible}**",
        f"- Calendar date: **{snap['target_calendar_date']}** ({args.timezone})",
        "",
        "## Totals (same window)",
        f"- discovered_today: **{tot['discovered_today']}**",
        f"- articles_extracted_today: **{tot['articles_extracted_today']}**",
        f"- remaining_estimate: **{tot['remaining_estimate']}**",
        f"- frontier_pending_today: **{tot['frontier_pending_today']}**",
        f"- frontier_failed_today: **{tot['frontier_failed_today']}**",
        f"- sources_with_article_today: **{src_with_article}**",
        "",
        "## Per source",
        "",
        "| source_id | discovered_today | articles_today | remaining_est | frontier_pending | frontier_failed |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for r in snap["rows"]:
        lines.append(
            f"| {r['source_id']} | {r['discovered_today']} | {r['articles_extracted_today']} | "
            f"{r['remaining_estimate']} | {r['frontier_pending_today']} | {r['frontier_failed_today']} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Đã ghi: {md_path.resolve()}")

    if args.csv_out is not None:
        args.csv_out.parent.mkdir(parents=True, exist_ok=True)
        with args.csv_out.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(
                fh,
                fieldnames=[
                    "source_id",
                    "discovered_today",
                    "articles_extracted_today",
                    "remaining_estimate",
                    "frontier_pending_today",
                    "frontier_failed_today",
                ],
            )
            w.writeheader()
            for r in snap["rows"]:
                w.writerow(r)
        print(f"CSV: {args.csv_out.resolve()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
