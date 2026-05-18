#!/usr/bin/env python3
"""Article counts per classified source from live DuckDB (source_profiles + articles).

Does not crawl. Uses the same web_intel.duckdb the profiler/crawler writes.

Windows note: if another process holds an exclusive lock on the DB file, open read_only
may fail — retry when the long crawl pauses or finishes.

Windows:
  --window week     : Monday 00:00 … now (timezone), published_at uses date only
  --window today    : single calendar day in --timezone (default real today); optional --calendar-date
  --window rolling  : last N days (extracted_at UTC naive, or published date for published metric)
"""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent


def _utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


def _week_bounds_local(tz_name: str) -> tuple[date, date, datetime, datetime]:
    """Return (week_start_date, today_date, start_utc_naive, end_utc_naive) for [Mon 00:00 TZ .. now TZ]."""
    tz = ZoneInfo(tz_name)
    now_local = datetime.now(tz)
    today_d = now_local.date()
    monday_d = today_d - timedelta(days=today_d.weekday())
    start_local = datetime.combine(monday_d, datetime.min.time(), tzinfo=tz)
    start_utc = start_local.astimezone(timezone.utc).replace(tzinfo=None)
    end_utc = now_local.astimezone(timezone.utc).replace(tzinfo=None)
    return monday_d, today_d, start_utc, end_utc


def _calendar_day_bounds_utc_naive(
    tz_name: str, target_day: date
) -> tuple[date, datetime, datetime]:
    """Inclusive calendar day in tz → [start_utc_naive, end_utc_naive_exclusive)."""
    tz = ZoneInfo(tz_name)
    start_local = datetime.combine(target_day, datetime.min.time(), tzinfo=tz)
    end_local_excl = start_local + timedelta(days=1)
    start_utc = start_local.astimezone(timezone.utc).replace(tzinfo=None)
    end_utc_excl = end_local_excl.astimezone(timezone.utc).replace(tzinfo=None)
    return target_day, start_utc, end_utc_excl


def main(argv: list[str] | None = None) -> int:
    _utf8_stdio()
    p = argparse.ArgumentParser(description="Weekly article counts per classified source (DuckDB)")
    p.add_argument("--db", type=Path, default=ROOT / "data" / "db" / "web_intel.duckdb")
    p.add_argument(
        "--window",
        choices=("week", "today", "rolling"),
        default="week",
        help="week | today | rolling",
    )
    p.add_argument("--days", type=int, default=7, help="With --window rolling: number of days")
    p.add_argument(
        "--calendar-date",
        default=None,
        metavar="YYYY-MM-DD",
        help="With --window today: calendar day (default: today in --timezone)",
    )
    p.add_argument("--timezone", default="Europe/Amsterdam", help="Calendar boundaries for week/today")
    p.add_argument(
        "--metric",
        choices=("published", "extracted"),
        default="published",
        help="published uses DATE(left(published_at,10)); extracted uses extracted_at UTC half-open range",
    )
    p.add_argument(
        "--only-active-profiles",
        action="store_true",
        help="Only source_profiles.status in active, active_candidate",
    )
    p.add_argument(
        "--classified-csv",
        type=Path,
        default=None,
        help="Optional: restrict to source_id listed in this CSV (e.g. export of profiles)",
    )
    p.add_argument("--md-out", type=Path, default=None)
    p.add_argument("--csv-out", type=Path, default=None)
    args = p.parse_args(argv)

    if not args.db.is_file():
        print(f"No DB file: {args.db}", file=sys.stderr)
        return 1

    try:
        import duckdb
    except ImportError as exc:
        print(exc, file=sys.stderr)
        return 1

    try:
        con = duckdb.connect(str(args.db), read_only=True)
    except Exception as exc:
        print(
            "Cannot open DuckDB read-only (another process may hold the file open):\n"
            f"  {exc}\n"
            "Try again when run_profile / crawl is idle, or use export CSV script instead.",
            file=sys.stderr,
        )
        return 2

    classified_csv_ids: list[str] | None = None
    if args.classified_csv is not None:
        if not args.classified_csv.is_file():
            print(f"Missing --classified-csv: {args.classified_csv}", file=sys.stderr)
            return 1
        classified_csv_ids = []
        with args.classified_csv.open(encoding="utf-8", newline="") as fh:
            r = csv.DictReader(fh)
            if not r.fieldnames or "source_id" not in r.fieldnames:
                print("classified CSV needs source_id column", file=sys.stderr)
                return 1
            for row in r:
                sid = (row.get("source_id") or "").strip()
                if sid:
                    classified_csv_ids.append(sid)

    status_clause = ""
    if args.only_active_profiles:
        status_clause = " AND status IN ('active', 'active_candidate')"

    if classified_csv_ids is not None:
        con.execute("CREATE TEMP TABLE _cls(source_id VARCHAR)")
        con.executemany("INSERT INTO _cls VALUES (?)", [(x,) for x in classified_csv_ids])
        profile_sql = f"""
            CREATE TEMP TABLE _profiles AS
            SELECT DISTINCT p.source_id
            FROM source_profiles p
            INNER JOIN _cls c ON c.source_id = p.source_id
            WHERE 1=1 {status_clause}
        """
    else:
        profile_sql = f"""
            CREATE TEMP TABLE _profiles AS
            SELECT DISTINCT source_id FROM source_profiles WHERE 1=1 {status_clause}
        """

    try:
        con.execute(profile_sql)

        if args.window == "week":
            monday_d, today_d, start_utc, end_utc = _week_bounds_local(args.timezone)
            if args.metric == "extracted":
                rows = con.execute(
                    """
                    SELECT p.source_id, COUNT(a.id) AS n
                    FROM _profiles p
                    LEFT JOIN articles a
                      ON a.source_id = p.source_id
                     AND a.extracted_at IS NOT NULL
                     AND a.extracted_at >= ?
                     AND a.extracted_at <= ?
                    GROUP BY p.source_id
                    ORDER BY n DESC, p.source_id
                    """,
                    [start_utc, end_utc],
                ).fetchall()
                hdr_window = (
                    f"extracted_at UTC range [{start_utc.isoformat()} .. {end_utc.isoformat()}] "
                    f"(calendar Mon→now in {args.timezone})"
                )
            else:
                rows = con.execute(
                    """
                    SELECT p.source_id, COUNT(a.id) AS n
                    FROM _profiles p
                    LEFT JOIN articles a
                      ON a.source_id = p.source_id
                     AND try_cast(left(trim(coalesce(a.published_at, '')), 10) AS DATE) IS NOT NULL
                     AND try_cast(left(trim(coalesce(a.published_at, '')), 10) AS DATE) >= ?::DATE
                     AND try_cast(left(trim(coalesce(a.published_at, '')), 10) AS DATE) <= ?::DATE
                    GROUP BY p.source_id
                    ORDER BY n DESC, p.source_id
                    """,
                    [monday_d.isoformat(), today_d.isoformat()],
                ).fetchall()
                hdr_window = (
                    f"published_at date in [{monday_d.isoformat()} .. {today_d.isoformat()}] "
                    f"(week Mon→today local {args.timezone})"
                )
        elif args.window == "today":
            tz = ZoneInfo(args.timezone)
            if args.calendar_date:
                target_d = date.fromisoformat(args.calendar_date)
            else:
                target_d = datetime.now(tz).date()
            target_day, start_utc, end_utc_excl = _calendar_day_bounds_utc_naive(args.timezone, target_d)
            if args.metric == "extracted":
                rows = con.execute(
                    """
                    SELECT p.source_id, COUNT(a.id) AS n
                    FROM _profiles p
                    LEFT JOIN articles a
                      ON a.source_id = p.source_id
                     AND a.extracted_at IS NOT NULL
                     AND a.extracted_at >= ?
                     AND a.extracted_at < ?
                    GROUP BY p.source_id
                    ORDER BY n DESC, p.source_id
                    """,
                    [start_utc, end_utc_excl],
                ).fetchall()
                hdr_window = (
                    f"extracted_at UTC [{start_utc.isoformat()} .. {end_utc_excl.isoformat()}) "
                    f"= calendar day {target_day.isoformat()} ({args.timezone})"
                )
            else:
                rows = con.execute(
                    """
                    SELECT p.source_id, COUNT(a.id) AS n
                    FROM _profiles p
                    LEFT JOIN articles a
                      ON a.source_id = p.source_id
                     AND try_cast(left(trim(coalesce(a.published_at, '')), 10) AS DATE) = ?::DATE
                    GROUP BY p.source_id
                    ORDER BY n DESC, p.source_id
                    """,
                    [target_day.isoformat()],
                ).fetchall()
                hdr_window = (
                    f"published_at date == {target_day.isoformat()} (calendar {args.timezone})"
                )
        else:
            days = max(1, args.days)
            if args.metric == "extracted":
                cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
                rows = con.execute(
                    """
                    SELECT p.source_id, COUNT(a.id) AS n
                    FROM _profiles p
                    LEFT JOIN articles a
                      ON a.source_id = p.source_id
                     AND a.extracted_at IS NOT NULL
                     AND a.extracted_at >= ?
                    GROUP BY p.source_id
                    ORDER BY n DESC, p.source_id
                    """,
                    [cutoff],
                ).fetchall()
                hdr_window = f"extracted_at >= {cutoff.isoformat()} UTC (rolling {days}d)"
            else:
                today_utc = datetime.now(timezone.utc).date()
                start_d = today_utc - timedelta(days=days - 1)
                rows = con.execute(
                    """
                    SELECT p.source_id, COUNT(a.id) AS n
                    FROM _profiles p
                    LEFT JOIN articles a
                      ON a.source_id = p.source_id
                     AND try_cast(left(trim(coalesce(a.published_at, '')), 10) AS DATE) IS NOT NULL
                     AND try_cast(left(trim(coalesce(a.published_at, '')), 10) AS DATE) >= ?::DATE
                     AND try_cast(left(trim(coalesce(a.published_at, '')), 10) AS DATE) <= ?::DATE
                    GROUP BY p.source_id
                    ORDER BY n DESC, p.source_id
                    """,
                    [start_d.isoformat(), today_utc.isoformat()],
                ).fetchall()
                hdr_window = f"published_at date [{start_d} .. {today_utc}] UTC-calendar rolling {days}d"

        prof_n = con.execute("SELECT COUNT(*) FROM _profiles").fetchone()[0]
        total = sum(r[1] for r in rows)
        nz = sum(1 for r in rows if r[1] > 0)

        print("")
        print("===== Classified sources · articles this window (live DuckDB) =====")
        print(f"- DB: {args.db}")
        print(f"- Profile sources counted: {prof_n}")
        print(f"- Window: {hdr_window}")
        print(f"- Metric: {args.metric}")
        if args.only_active_profiles:
            print("- Profiles filter: status active | active_candidate")
        if classified_csv_ids is not None:
            print(f"- Restricted to --classified-csv ({len(classified_csv_ids)} ids listed)")
        print(f"- Sources with >=1 article: {nz}")
        print(f"- Total articles (LEFT JOIN count): {total}")
        print("")
        print("source_id | articles")
        print("--- | ---:")
        for sid, n in rows:
            print(f"{sid} | {n}")
        print("")

        if args.md_out is not None:
            args.md_out.parent.mkdir(parents=True, exist_ok=True)
            lines = [
                "# Articles per classified source (DuckDB)",
                "",
                f"- {hdr_window}",
                f"- Metric: **{args.metric}**",
                f"- Profile rows: **{prof_n}** · Sources with articles: **{nz}** · Total: **{total}**",
                "",
                "| source_id | articles |",
                "| --- | ---: |",
            ]
            for sid, n in rows:
                lines.append(f"| {sid} | {n} |")
            args.md_out.write_text("\n".join(lines) + "\n", encoding="utf-8")
            print(f"Wrote: {args.md_out.resolve()}")

        if args.csv_out is not None:
            args.csv_out.parent.mkdir(parents=True, exist_ok=True)
            with args.csv_out.open("w", encoding="utf-8", newline="") as fh:
                w = csv.writer(fh)
                w.writerow(["source_id", "articles"])
                w.writerows(rows)
            print(f"CSV: {args.csv_out.resolve()}")

        return 0
    finally:
        con.close()


if __name__ == "__main__":
    raise SystemExit(main())
