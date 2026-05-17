#!/usr/bin/env python3
"""Today full-article crawl orchestrator (profile → Scrapy today mode → exports)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from reporting.crawl_report import write_final_crawl_report  # noqa: E402
from storage.db import WebIntelDB, new_id  # noqa: E402


def build_today_commands(
    *,
    python_executable: str,
    input_path: Path,
    profile_limit: int,
    strategy: str,
    force_refresh: bool,
    run_id: str,
    date_arg: str,
    timezone_arg: str,
    max_urls_per_source: int,
    close_spider_timeout: int,
) -> list[list[str]]:
    profile_cmd = [
        python_executable,
        "run_profile.py",
        "--input",
        str(input_path),
        "--profile-only",
        "--limit",
        str(profile_limit),
    ]
    if force_refresh:
        profile_cmd.append("--force-refresh")

    scrapy_cmd = [
        python_executable,
        "run_scrapy.py",
        "--strategy",
        strategy,
        "--limit",
        str(profile_limit),
        "--today-only",
        "--date",
        date_arg,
        "--timezone",
        timezone_arg,
        "--max-urls-per-source",
        str(max_urls_per_source),
        "--close-spider-timeout",
        str(close_spider_timeout),
        "--run-id",
        run_id,
    ]

    export_cmd = [
        python_executable,
        "run_export.py",
        "--today-only",
        "--date",
        date_arg,
        "--timezone",
        timezone_arg,
    ]

    return [profile_cmd, scrapy_cmd, export_cmd]


def _run_step(cmd: list[str], *, timeout_seconds: int | None) -> tuple[int, bool]:
    print("")
    print("===== RUNNING =====")
    print(" ".join(cmd))
    timeout: float | None = float(timeout_seconds) if timeout_seconds is not None else None
    try:
        completed = subprocess.run(cmd, cwd=ROOT, timeout=timeout)  # noqa: S603
    except subprocess.TimeoutExpired:
        print("")
        print("===== STEP TIMEOUT =====")
        print("Command:", " ".join(cmd))
        if timeout_seconds is not None:
            print(f"Exceeded {timeout_seconds}s; subprocess terminated.")
        return 124, True
    if completed.returncode != 0:
        print("")
        print("===== STEP FAILED =====")
        print("Command:", " ".join(cmd))
        print("Return code:", completed.returncode)
    return int(completed.returncode), False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Leon Web Intel — today full public-discovery crawl")
    parser.add_argument("--input", type=Path, default=ROOT / "config" / "sources_raw.txt")
    parser.add_argument("--strategy", choices=("rss", "sitemap", "html", "all"), default="all")
    parser.add_argument("--date", default="today", help='YYYY-MM-DD or "today"')
    parser.add_argument("--timezone", default="Europe/Amsterdam", metavar="TZ")
    parser.add_argument("--profile-limit", type=int, default=198)
    parser.add_argument("--max-urls-per-source", type=int, default=1000)
    parser.add_argument("--step-timeout-seconds", type=int, default=None)
    parser.add_argument("--close-spider-timeout", type=int, default=1200)
    parser.add_argument("--force-refresh", action="store_true")
    args = parser.parse_args(argv)
    if args.max_urls_per_source <= 0:
        parser.error("--max-urls-per-source must be positive")
    if args.close_spider_timeout <= 0:
        parser.error("--close-spider-timeout must be positive")

    run_id = new_id()
    db_path = ROOT / "data" / "db" / "web_intel.duckdb"
    db = WebIntelDB(db_path)
    try:
        db.create_crawl_run(
            run_id=run_id,
            input_path=str(args.input),
            strategy=args.strategy,
            limit_sources=args.profile_limit,
            max_articles_per_source=args.max_urls_per_source,
            force_refresh=bool(args.force_refresh),
            config_json=json.dumps(
                {
                    "mode": "today_full_article",
                    "input": str(args.input),
                    "profile_limit": args.profile_limit,
                    "strategy": args.strategy,
                    "date": args.date,
                    "timezone": args.timezone,
                    "max_urls_per_source": args.max_urls_per_source,
                    "step_timeout_seconds": args.step_timeout_seconds,
                    "close_spider_timeout": args.close_spider_timeout,
                    "force_refresh": bool(args.force_refresh),
                },
                sort_keys=True,
            ),
            notes="run_today.py",
        )
    finally:
        db.close()

    commands = build_today_commands(
        python_executable=sys.executable,
        input_path=args.input,
        profile_limit=args.profile_limit,
        strategy=args.strategy,
        force_refresh=bool(args.force_refresh),
        run_id=run_id,
        date_arg=args.date,
        timezone_arg=args.timezone,
        max_urls_per_source=args.max_urls_per_source,
        close_spider_timeout=args.close_spider_timeout,
    )

    for cmd in commands:
        rc, timed_out = _run_step(cmd, timeout_seconds=args.step_timeout_seconds)
        if timed_out:
            fail_db = WebIntelDB(db_path)
            try:
                fail_db.finish_crawl_run(
                    run_id=run_id,
                    status="failed",
                    notes=f"step timeout after {args.step_timeout_seconds}s: {' '.join(cmd)}",
                )
            finally:
                fail_db.close()
            recovery = [
                sys.executable,
                "run_export.py",
                "--today-only",
                "--date",
                args.date,
                "--timezone",
                args.timezone,
            ]
            ex_rc, ex_to = _run_step(recovery, timeout_seconds=None)
            _run_step([sys.executable, "run_export.py"], timeout_seconds=None)
            ok_db = WebIntelDB(db_path)
            try:
                ok_db.update_source_health_from_current_db()
                write_final_crawl_report(ok_db, ROOT / "data" / "exports" / "final_crawl_report.md")
            finally:
                ok_db.close()
            if ex_to:
                return 124
            return 124 if ex_rc == 0 else ex_rc
        if rc != 0:
            fail_db = WebIntelDB(db_path)
            try:
                fail_db.finish_crawl_run(
                    run_id=run_id,
                    status="failed",
                    notes=f"command failed rc={rc}: {' '.join(cmd)}",
                )
            finally:
                fail_db.close()
            recovery_today = [
                sys.executable,
                "run_export.py",
                "--today-only",
                "--date",
                args.date,
                "--timezone",
                args.timezone,
            ]
            _run_step(recovery_today, timeout_seconds=None)
            _run_step([sys.executable, "run_export.py"], timeout_seconds=None)
            return rc

    final_report = ROOT / "data" / "exports" / "final_crawl_report.md"
    ok_db = WebIntelDB(db_path)
    try:
        ok_db.update_source_health_from_current_db()
        ok_db.finish_crawl_run(run_id=run_id, status="success", notes="")
        write_final_crawl_report(ok_db, final_report)
    finally:
        ok_db.close()

    print("")
    print("===== TODAY PIPELINE COMPLETE =====")
    print(f"Run ID: {run_id}")
    print(f"Final report: {final_report.resolve()}")
    print(f"Today slice: {(ROOT / 'data' / 'exports' / 'today_final_report.md').resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
