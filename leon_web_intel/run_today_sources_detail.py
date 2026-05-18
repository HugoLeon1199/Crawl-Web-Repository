#!/usr/bin/env python3
"""Per-source counts for one calendar day (timezone): articles, api_records, discovered_urls, crawl diagnostics."""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from utils.today_filter import resolve_calendar_date, target_date_range


def _utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


def _utc_naive(dt: datetime) -> datetime:
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def main() -> int:
    _utf8_stdio()
    p = argparse.ArgumentParser()
    p.add_argument("--db", type=Path, default=ROOT / "data" / "db" / "web_intel.duckdb")
    p.add_argument("--timezone", default="Europe/Amsterdam")
    p.add_argument(
        "--calendar-date",
        default=None,
        metavar="YYYY-MM-DD",
        help="Default: today in timezone",
    )
    p.add_argument("--md-out", type=Path, default=ROOT / "data" / "exports" / "articles_today_detail.md")
    p.add_argument("--csv-out", type=Path, default=ROOT / "data" / "exports" / "articles_today_detail.csv")
    args = p.parse_args()

    target_d: date = resolve_calendar_date(args.calendar_date, args.timezone)
    start_utc, end_utc_excl = target_date_range(args.calendar_date, args.timezone)
    start_naive = _utc_naive(start_utc)
    end_naive = _utc_naive(end_utc_excl)
    target_cal_str = target_d.isoformat()

    try:
        import duckdb
    except ImportError as exc:
        print(exc, file=sys.stderr)
        return 1

    try:
        con = duckdb.connect(str(args.db), read_only=True)
    except Exception as exc:
        print(f"Cannot open DB: {exc}", file=sys.stderr)
        return 2

    sql = """
        WITH prof AS (
          SELECT DISTINCT source_id, best_strategy, status
          FROM source_profiles
        ),
        art AS (
          SELECT
            source_id,
            COUNT(*) FILTER (
              WHERE extracted_at IS NOT NULL
                AND extracted_at >= ?
                AND extracted_at < ?
            ) AS extracted_today,
            COUNT(*) FILTER (
              WHERE try_cast(left(trim(coalesce(published_at, '')), 10) AS DATE) = ?::DATE
            ) AS published_today
          FROM articles
          GROUP BY source_id
        ),
        api AS (
          SELECT source_id, COUNT(*) AS api_records_today
          FROM api_records
          WHERE target_calendar_date = ?
            AND timezone_name = ?
            AND source_id IS NOT NULL
            AND trim(source_id) <> ''
          GROUP BY source_id
        ),
        disc AS (
          SELECT source_id, COUNT(*) AS discovered_today
          FROM discovered_urls
          WHERE discovered_at IS NOT NULL
            AND discovered_at >= ?
            AND discovered_at < ?
          GROUP BY source_id
        ),
        cerr AS (
          SELECT source_id, COUNT(*) AS crawl_errors_today
          FROM crawl_errors
          WHERE created_at IS NOT NULL
            AND created_at >= ?
            AND created_at < ?
          GROUP BY source_id
        ),
        front AS (
          SELECT source_id, COUNT(*) AS frontier_touch_today
          FROM crawl_frontier
          WHERE last_seen_at IS NOT NULL
            AND last_seen_at >= ?
            AND last_seen_at < ?
          GROUP BY source_id
        )
        SELECT
          p.source_id,
          p.best_strategy,
          p.status,
          COALESCE(a.extracted_today, 0)::BIGINT AS extracted_today,
          COALESCE(a.published_today, 0)::BIGINT AS published_today,
          COALESCE(api.api_records_today, 0)::BIGINT AS api_records_today,
          COALESCE(disc.discovered_today, 0)::BIGINT AS discovered_today,
          COALESCE(cerr.crawl_errors_today, 0)::BIGINT AS crawl_errors_today,
          COALESCE(front.frontier_touch_today, 0)::BIGINT AS frontier_touch_today
        FROM prof p
        LEFT JOIN art a ON a.source_id = p.source_id
        LEFT JOIN api api ON api.source_id = p.source_id
        LEFT JOIN disc disc ON disc.source_id = p.source_id
        LEFT JOIN cerr cerr ON cerr.source_id = p.source_id
        LEFT JOIN front front ON front.source_id = p.source_id
        ORDER BY (
          COALESCE(a.extracted_today, 0)
          + COALESCE(api.api_records_today, 0)
          + COALESCE(disc.discovered_today, 0)
        ) DESC, p.source_id
        """

    params = [
        start_naive,
        end_naive,
        target_cal_str,
        target_cal_str,
        args.timezone,
        start_naive,
        end_naive,
        start_naive,
        end_naive,
        start_naive,
        end_naive,
    ]
    rows_raw = con.execute(sql, params).fetchall()

    api_no_source = int(
        con.execute(
            """
            SELECT COUNT(*)::BIGINT
            FROM api_records
            WHERE target_calendar_date = ?
              AND timezone_name = ?
              AND (source_id IS NULL OR trim(source_id) = '')
            """,
            [target_cal_str, args.timezone],
        ).fetchone()[0]
    )

    api_no_source_by_adapter = con.execute(
        """
        SELECT api_name, COUNT(*)::BIGINT AS n
        FROM api_records
        WHERE target_calendar_date = ?
          AND timezone_name = ?
          AND (source_id IS NULL OR trim(source_id) = '')
        GROUP BY api_name
        ORDER BY n DESC, api_name
        """,
        [target_cal_str, args.timezone],
    ).fetchall()

    gdelt_today = int(
        con.execute(
            """
            SELECT COUNT(*)::BIGINT
            FROM gdelt_doc_hits
            WHERE target_calendar_date = ?
              AND timezone_name = ?
            """,
            [target_cal_str, args.timezone],
        ).fetchone()[0]
    )

    con.close()

    rows_out: list[tuple] = []
    for sid, strat, st, ex, pub, api_n, disc_n, cerr_n, front_n in rows_raw:
        intake = int(ex) + int(api_n) + int(disc_n)
        rows_out.append((sid, strat, st, ex, pub, api_n, disc_n, cerr_n, front_n, intake))

    tot_ext = sum(r[3] for r in rows_out)
    tot_pub = sum(r[4] for r in rows_out)
    tot_api = sum(r[5] for r in rows_out)
    tot_disc = sum(r[6] for r in rows_out)
    tot_err = sum(r[7] for r in rows_out)
    tot_front = sum(r[8] for r in rows_out)
    tot_intake_prof = sum(r[9] for r in rows_out)

    nz_any = sum(
        1
        for r in rows_out
        if r[3] > 0 or r[4] > 0 or r[5] > 0 or r[6] > 0 or r[7] > 0 or r[8] > 0
    )

    gap_rows = [r for r in rows_out if r[9] == 0]
    gap_rows.sort(key=lambda r: r[0])

    lines = [
        "# Full-day pipeline stats per source (DuckDB)",
        "",
        f"- Timezone: **{args.timezone}**",
        f"- Calendar day: **{target_cal_str}**",
        f"- **extracted_today**: `articles.extracted_at` ∈ `[{start_naive.isoformat()}, {end_naive.isoformat()})` UTC",
        f"- **published_today**: `DATE(left(published_at,10))` = `{target_cal_str}`",
        f"- **api_records_today**: `api_records` where `target_calendar_date` + `timezone_name` match",
        f"- **discovered_today**: `discovered_urls.discovered_at` in the same UTC half-open window",
        f"- **crawl_errors_today** / **frontier_touch_today**: `created_at` / `last_seen_at` in that window",
        "",
        f"- Sources in `source_profiles`: **{len(rows_out)}**",
        f"- Sources with any non-zero column: **{nz_any}**",
        "",
        "## Totals (sources listed above)",
        "",
        f"- Sum **extracted_today**: **{tot_ext}**",
        f"- Sum **published_today**: **{tot_pub}**",
        f"- Sum **api_records_today** (with `source_id`): **{tot_api}**",
        f"- Sum **discovered_today**: **{tot_disc}**",
        f"- Sum **crawl_errors_today**: **{tot_err}**",
        f"- Sum **frontier_touch_today**: **{tot_front}**",
        f"- **intake_sum** (extracted + api + discovered, per row): **{tot_intake_prof}**",
        "",
        "## Outside profile sources",
        "",
        f"- **api_records** with missing/empty `source_id` (same calendar filter): **{api_no_source}**",
    ]
    if api_no_source_by_adapter:
        lines.append("")
        lines.append("| api_name | count |")
        lines.append("| --- | ---: |")
        for name, n in api_no_source_by_adapter:
            lines.append(f"| {name or '(empty)'} | {n} |")

    lines.extend(
        [
            "",
            "## GDELT (global for day, not per-source)",
            "",
            f"- **gdelt_doc_hits** rows: **{gdelt_today}**",
            "",
            "| source_id | best_strategy | status | extracted_today | published_today | api_records_today | discovered_today | crawl_errors_today | frontier_touch_today | intake_sum |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for sid, strat, st, ex, pub, api_n, disc_n, cerr_n, front_n, intake in rows_out:
        strat_s = strat or ""
        st_s = st or ""
        lines.append(
            f"| {sid} | {strat_s} | {st_s} | {ex} | {pub} | {api_n} | {disc_n} | {cerr_n} | {front_n} | {intake} |"
        )

    lines.extend(
        [
            "",
            "## Gap sources (`intake_sum` = 0)",
            "",
            "Không có bản ghi **articles** (extract trong cửa sổ), **api_records** (đúng `target_calendar_date`), "
            "hay **discovered_urls** trong ngày — cần crawl/API lại hoặc kiểm tra profile/strategy.",
            "",
            f"- **{len(gap_rows)}** / **{len(rows_out)}** source trong `source_profiles`.",
            "",
            "| source_id | best_strategy | status | crawl_errors_today | frontier_touch_today |",
            "| --- | --- | --- | ---: | ---: |",
        ]
    )
    for sid, strat, st, _ex, _pub, _api_n, _disc_n, cerr_n, front_n, _intake in gap_rows:
        lines.append(f"| {sid} | {strat or ''} | {st or ''} | {cerr_n} | {front_n} |")

    gap_csv = args.md_out.parent / f"source_intake_gaps_{target_cal_str}.csv"
    with gap_csv.open("w", encoding="utf-8", newline="") as gfh:
        gw = csv.writer(gfh)
        gw.writerow(
            [
                "source_id",
                "best_strategy",
                "status",
                "crawl_errors_today",
                "frontier_touch_today",
                "note",
            ]
        )
        for sid, strat, st, _ex, _pub, _api_n, _disc_n, cerr_n, front_n, _intake in gap_rows:
            gw.writerow([sid, strat or "", st or "", cerr_n, front_n, "intake_sum=0"])

    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    hdr = [
        "source_id",
        "best_strategy",
        "status",
        "extracted_today",
        "published_today",
        "api_records_today",
        "discovered_today",
        "crawl_errors_today",
        "frontier_touch_today",
        "intake_sum",
    ]
    with args.csv_out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(hdr)
        w.writerows(rows_out)
        w.writerow([])
        w.writerow(
            ["__TOTALS_PROFILE_SOURCES__", "", "", tot_ext, tot_pub, tot_api, tot_disc, tot_err, tot_front, tot_intake_prof]
        )
        w.writerow(
            ["__EXTRA__", "api_records_missing_source_id", "", "", "", api_no_source, "", "", "", ""]
        )

    print("")
    print(f"Calendar day {target_cal_str} ({args.timezone})")
    print(f"UTC window [{start_naive} .. {end_naive}) exclusive end")
    print(f"Sources: {len(rows_out)} | any non-zero: {nz_any}")
    print(
        f"Totals (profile sources): extracted={tot_ext} published={tot_pub} api={tot_api} "
        f"discovered={tot_disc} errors={tot_err} frontier={tot_front} intake_sum={tot_intake_prof}"
    )
    print(f"API rows without source_id: {api_no_source} | gdelt_doc_hits: {gdelt_today}")
    print(f"Gap sources (intake_sum=0): {len(gap_rows)} — CSV: {gap_csv.resolve()}")
    print("")
    print("source_id | strategy | ext | pub | api | disc | err | front | intake")
    print("--- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---:")
    for sid, strat, st, ex, pub, api_n, disc_n, cerr_n, front_n, intake in rows_out[:25]:
        print(f"{sid} | {strat or ''} | {ex} | {pub} | {api_n} | {disc_n} | {cerr_n} | {front_n} | {intake}")
    if len(rows_out) > 25:
        print(f"... +{len(rows_out) - 25} rows (full table in exports)")
    print("")
    print(f"MD:  {args.md_out.resolve()}")
    print(f"CSV: {args.csv_out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
