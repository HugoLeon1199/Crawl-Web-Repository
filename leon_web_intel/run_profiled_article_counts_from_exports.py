#!/usr/bin/env python3
"""Count articles per classified source using export CSVs only (no DuckDB, no crawl).

Reads:
  - data/exports/source_profiles.csv (source_id + optional status filter)
  - data/exports/articles_metadata.csv (source_id, published_at, extracted_at)

Default window: rolling last --days calendar days (published_at date only, local calendar).
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


def _parse_profile_statuses(path: Path, *, only_active: bool) -> set[str]:
    out: set[str] = set()
    with path.open(encoding="utf-8", newline="") as fh:
        r = csv.DictReader(fh)
        if not r.fieldnames or "source_id" not in r.fieldnames:
            raise ValueError(f"{path.name}: missing source_id column")
        for row in r:
            sid = (row.get("source_id") or "").strip()
            if not sid:
                continue
            if only_active:
                st = (row.get("status") or "").strip().lower()
                if st not in ("active", "active_candidate"):
                    continue
            out.add(sid)
    return out


_DATE_ONLY = re.compile(r"^(\d{4}-\d{2}-\d{2})$")


def _parse_published_day(val: str | None) -> date | None:
    if not val:
        return None
    s = val.strip()
    if not s:
        return None
    m = _DATE_ONLY.match(s[:10])
    if m:
        try:
            return date.fromisoformat(m.group(1))
        except ValueError:
            return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is not None:
            dt = dt.astimezone(tz=None).replace(tzinfo=None)
        return dt.date()
    except ValueError:
        return None


def _parse_extracted_naive_utc(val: str | None) -> datetime | None:
    if not val:
        return None
    s = val.strip()
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", ""))
    except ValueError:
        return None


def main(argv: list[str] | None = None) -> int:
    _utf8_stdio()
    p = argparse.ArgumentParser(description="Article counts per profiled source from CSV exports only")
    p.add_argument("--profiles", type=Path, default=ROOT / "data" / "exports" / "source_profiles.csv")
    p.add_argument("--articles", type=Path, default=ROOT / "data" / "exports" / "articles_metadata.csv")
    p.add_argument("--days", type=int, default=7, help="Rolling window length (calendar days)")
    p.add_argument(
        "--metric",
        choices=("published", "extracted"),
        default="published",
        help="published: by published_at date in window; extracted: by extracted_at last N days (UTC)",
    )
    p.add_argument(
        "--only-active-profiles",
        action="store_true",
        help="Restrict to profiles with status active or active_candidate",
    )
    p.add_argument(
        "--md-out",
        type=Path,
        default=ROOT / "data" / "exports" / "articles_per_profiled_source_last_week.md",
    )
    p.add_argument("--csv-out", type=Path, default=None)
    args = p.parse_args(argv)

    if not args.profiles.is_file():
        print(f"Missing profiles CSV: {args.profiles}", file=sys.stderr)
        return 1
    if not args.articles.is_file():
        print(f"Missing articles CSV: {args.articles}", file=sys.stderr)
        return 1

    try:
        profile_ids = _parse_profile_statuses(args.profiles, only_active=args.only_active_profiles)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1

    today = date.today()
    start_day = today - timedelta(days=max(1, args.days) - 1)
    counts: dict[str, int] = defaultdict(int)
    skipped_pub = 0
    rows_seen = 0

    with args.articles.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        fields = set(reader.fieldnames or [])
        if "source_id" not in fields:
            print("articles CSV missing source_id", file=sys.stderr)
            return 1
        if args.metric == "extracted" and "extracted_at" not in fields:
            print("articles CSV missing extracted_at", file=sys.stderr)
            return 1

        for row in reader:
            rows_seen += 1
            sid = (row.get("source_id") or "").strip()
            if sid not in profile_ids:
                continue
            if args.metric == "published":
                pd = _parse_published_day(row.get("published_at"))
                if pd is None:
                    skipped_pub += 1
                    continue
                if start_day <= pd <= today:
                    counts[sid] += 1
            else:
                ext = _parse_extracted_naive_utc(row.get("extracted_at"))
                if ext is None:
                    continue
                cutoff_dt = datetime.utcnow() - timedelta(days=max(1, args.days))
                if ext >= cutoff_dt:
                    counts[sid] += 1

    pairs = [(sid, counts.get(sid, 0)) for sid in sorted(profile_ids)]
    pairs.sort(key=lambda x: (-x[1], x[0]))

    total_art = sum(counts.values())
    with_article = sum(1 for sid in profile_ids if counts.get(sid, 0) > 0)

    print("")
    print("===== Articles per classified source (exports only — no DB, no crawl) =====")
    print(f"- Profiles: {args.profiles.name}")
    print(f"- Articles metadata rows scanned: {rows_seen}")
    print(f"- Profiled sources{' (active only)' if args.only_active_profiles else ''}: {len(profile_ids)}")
    print(f"- Metric: {args.metric}")
    if args.metric == "published":
        print(f"- Published date window (local): {start_day.isoformat()} .. {today.isoformat()} ({args.days} days)")
        print(f"- Skipped rows (unparsed published_at): {skipped_pub}")
    else:
        print(f"- extracted_at >= now_utc - {args.days}d (naive UTC stamps in CSV)")
    print(f"- Sources with >=1 article: {with_article}")
    print(f"- Total articles counted: {total_art}")
    print("")
    print("source_id | articles")
    print("--- | ---:")
    for sid, n in pairs:
        print(f"{sid} | {n}")
    print("")

    if args.md_out is not None:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Articles per profiled source (from exports)",
            "",
            f"- Profiles file: `{args.profiles.name}`",
            f"- Articles file: `{args.articles.name}`",
            f"- Metric: **{args.metric}**",
            f"- Window: **{start_day.isoformat()}** … **{today.isoformat()}** ({args.days} days, published metric uses local dates)",
            f"- Profiled sources: **{len(profile_ids)}** · With articles: **{with_article}** · Total rows: **{total_art}**",
            "",
            "| source_id | articles |",
            "| --- | ---: |",
        ]
        for sid, n in pairs:
            lines.append(f"| {sid} | {n} |")
        args.md_out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"Wrote: {args.md_out.resolve()}")

    if args.csv_out is not None:
        args.csv_out.parent.mkdir(parents=True, exist_ok=True)
        with args.csv_out.open("w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["source_id", "articles"])
            w.writerows(pairs)
        print(f"CSV: {args.csv_out.resolve()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
