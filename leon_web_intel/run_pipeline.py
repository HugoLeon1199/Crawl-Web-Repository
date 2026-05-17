#!/usr/bin/env python3
"""End-to-end crawl foundation orchestrator."""

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


def build_pipeline_commands(
    *,
    python_executable: str,
    input_path: Path,
    limit: int | None,
    max_articles_per_source: int,
    strategy: str,
    force_refresh: bool,
    run_id: str,
    close_spider_timeout: int,
) -> list[list[str]]:
    profile_cmd = [
        python_executable,
        "run_profile.py",
        "--input",
        str(input_path),
        "--profile-only",
    ]
    if limit is not None:
        profile_cmd.extend(["--limit", str(limit)])
    if force_refresh:
        profile_cmd.append("--force-refresh")

    scrapy_cmd = [
        python_executable,
        "run_scrapy.py",
        "--strategy",
        strategy,
        "--limit",
        str(limit if limit is not None else 0),
        "--max-articles-per-source",
        str(max_articles_per_source),
        "--close-spider-timeout",
        str(close_spider_timeout),
        "--run-id",
        run_id,
    ]

    return [
        profile_cmd,
        scrapy_cmd,
        [python_executable, "run_export.py"],
    ]


def _run_step(cmd: list[str], *, timeout_seconds: int | None) -> tuple[int, bool]:
    """Run one subprocess step. Returns ``(returncode, timed_out)``."""
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
    parser = argparse.ArgumentParser(description="Leon Web Intel E2E crawl foundation")
    parser.add_argument("--input", type=Path, default=ROOT / "config" / "sources_raw.txt")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--max-articles-per-source", type=int, default=3)
    parser.add_argument("--strategy", choices=("rss", "sitemap", "html", "all"), default="all")
    parser.add_argument("--force-refresh", action="store_true")
    parser.add_argument(
        "--step-timeout-seconds",
        type=int,
        default=None,
        metavar="SEC",
        help=(
            "Wall-clock cap per pipeline subprocess step (profile, scrapy, export). "
            "On timeout the step is killed, crawl_run marked failed, and run_export.py "
            "is still executed once without this cap for a partial export."
        ),
    )
    parser.add_argument(
        "--close-spider-timeout",
        type=int,
        default=600,
        metavar="SEC",
        help="Forwarded to run_scrapy.py as Scrapy CLOSESPIDER_TIMEOUT (seconds).",
    )
    args = parser.parse_args(argv)
    if args.step_timeout_seconds is not None and args.step_timeout_seconds <= 0:
        parser.error("--step-timeout-seconds must be positive when set")
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
            limit_sources=args.limit,
            max_articles_per_source=args.max_articles_per_source,
            force_refresh=bool(args.force_refresh),
            config_json=json.dumps(
                {
                    "input": str(args.input),
                    "limit": args.limit,
                    "max_articles_per_source": args.max_articles_per_source,
                    "strategy": args.strategy,
                    "force_refresh": bool(args.force_refresh),
                    "step_timeout_seconds": args.step_timeout_seconds,
                    "close_spider_timeout": args.close_spider_timeout,
                },
                sort_keys=True,
            ),
            notes="",
        )
    finally:
        db.close()

    commands = build_pipeline_commands(
        python_executable=sys.executable,
        input_path=args.input,
        limit=args.limit,
        max_articles_per_source=args.max_articles_per_source,
        strategy=args.strategy,
        force_refresh=bool(args.force_refresh),
        run_id=run_id,
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
                    notes=(
                        f"step timeout after {args.step_timeout_seconds}s: {' '.join(cmd)}"
                    ),
                )
            finally:
                fail_db.close()
            export_cmd = [sys.executable, "run_export.py"]
            ex_rc, ex_timed_out = _run_step(export_cmd, timeout_seconds=None)
            if ex_timed_out:
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
    print("===== PIPELINE COMPLETE =====")
    print(f"Run ID: {run_id}")
    print(f"Final report: {final_report.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
