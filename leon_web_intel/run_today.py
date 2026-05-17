#!/usr/bin/env python3
"""Today full-article crawl orchestrator (optional GDELT → profile → Scrapy today mode → exports)."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from reporting.crawl_report import write_final_crawl_report  # noqa: E402
from storage.db import WebIntelDB, new_id  # noqa: E402
from utils.full_run import profile_limit_arg, resolve_max_urls_per_source  # noqa: E402

EXPORT_META = ROOT / "data" / "exports" / "today_run_meta.json"


def count_raw_source_lines(path: Path) -> int:
    if not path.is_file():
        return 0
    n = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            n += 1
    return n


def build_gdelt_command(
    *,
    python_executable: str,
    date_arg: str,
    timezone_arg: str,
    query: str,
    max_records: int,
    extract_content: bool,
) -> list[str]:
    cmd = [
        python_executable,
        "run_gdelt_today.py",
        "--date",
        date_arg,
        "--timezone",
        timezone_arg,
        "--query",
        query,
        "--max-records",
        str(max_records),
    ]
    if extract_content:
        cmd.append("--extract-content")
    return cmd


def build_api_hub_command(
    *,
    python_executable: str,
    date_arg: str,
    timezone_arg: str,
    apis: str,
    api_query: str,
    api_max_records: int,
    api_extract_content: bool,
) -> list[str]:
    cmd = [
        python_executable,
        "run_api_today.py",
        "--date",
        date_arg,
        "--timezone",
        timezone_arg,
        "--apis",
        apis,
        "--query",
        api_query,
        "--max-records",
        str(api_max_records),
    ]
    if api_extract_content:
        cmd.append("--extract-content")
    return cmd


def build_today_commands(
    *,
    python_executable: str,
    input_path: Path,
    profile_limit_cli: int,
    strategy: str,
    force_refresh: bool,
    run_id: str,
    date_arg: str,
    timezone_arg: str,
    max_urls_per_source_resolved: int,
    close_spider_timeout: int,
    profile_concurrency: int | None,
    skip_profile: bool,
) -> list[list[str]]:
    commands: list[list[str]] = []
    if not skip_profile:
        profile_cmd = [
            python_executable,
            "run_profile.py",
            "--input",
            str(input_path),
            "--profile-only",
        ]
        lim = profile_limit_arg(profile_limit_cli)
        if lim is not None and lim > 0:
            profile_cmd.extend(["--limit", str(lim)])
        if force_refresh:
            profile_cmd.append("--force-refresh")
        if profile_concurrency is not None:
            profile_cmd.extend(["--concurrency", str(profile_concurrency)])
        commands.append(profile_cmd)

    scrapy_cmd = [
        python_executable,
        "run_scrapy.py",
        "--strategy",
        strategy,
        "--limit",
        str(profile_limit_cli),
        "--today-only",
        "--date",
        date_arg,
        "--timezone",
        timezone_arg,
        "--max-urls-per-source",
        str(max_urls_per_source_resolved),
        "--close-spider-timeout",
        str(close_spider_timeout),
        "--run-id",
        run_id,
    ]
    commands.append(scrapy_cmd)

    export_cmd = [
        python_executable,
        "run_export.py",
        "--today-only",
        "--date",
        date_arg,
        "--timezone",
        timezone_arg,
    ]
    commands.append(export_cmd)
    return commands


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


def _write_run_meta(
    *, run_id: str, argv_repr: list[str], full_cmd: str, extra: dict | None = None
) -> None:
    EXPORT_META.parent.mkdir(parents=True, exist_ok=True)
    payload: dict = {"run_id": run_id, "argv": argv_repr, "full_run_command": full_cmd}
    if extra:
        payload.update(extra)
    EXPORT_META.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Leon Web Intel — today full public-discovery crawl")
    parser.add_argument("--input", type=Path, default=ROOT / "config" / "sources_raw.txt")
    parser.add_argument("--strategy", choices=("rss", "sitemap", "html", "all"), default="all")
    parser.add_argument("--date", default="today", help='YYYY-MM-DD or "today"')
    parser.add_argument("--timezone", default="Europe/Amsterdam", metavar="TZ")
    parser.add_argument(
        "--profile-limit",
        type=int,
        default=0,
        help="Max sources from input file (0 = all)",
    )
    parser.add_argument(
        "--max-urls-per-source",
        type=int,
        default=0,
        help="Per-source URL cap in today mode (0 = full-run ceiling)",
    )
    parser.add_argument("--step-timeout-seconds", type=int, default=None)
    parser.add_argument("--close-spider-timeout", type=int, default=10800)
    parser.add_argument("--force-refresh", action="store_true")
    parser.add_argument("--skip-profile", action="store_true", help="Skip run_profile.py (reuse DuckDB profiles)")
    parser.add_argument(
        "--profile-concurrency",
        type=int,
        default=None,
        metavar="N",
        help="Override YAML profiler concurrency for this run",
    )
    parser.add_argument("--include-gdelt", action="store_true", help="Run run_gdelt_today.py before profiling")
    parser.add_argument("--gdelt-query", default="*")
    parser.add_argument("--gdelt-max-records", type=int, default=0)
    parser.add_argument("--gdelt-extract-content", action="store_true")
    parser.add_argument(
        "--include-apis",
        action="store_true",
        help="Run run_api_today.py (API Hub) before profiling / Scrapy",
    )
    parser.add_argument("--apis", default="all", help="Passed to run_api_today (--apis)")
    parser.add_argument("--api-query", default="*")
    parser.add_argument("--api-max-records", type=int, default=0)
    parser.add_argument("--api-extract-content", action="store_true")
    args = parser.parse_args(argv)

    if args.close_spider_timeout <= 0:
        parser.error("--close-spider-timeout must be positive")

    max_urls_eff = resolve_max_urls_per_source(args.max_urls_per_source)

    raw_source_lines = count_raw_source_lines(args.input)

    eff_argv = list(sys.argv[1:] if argv is None else argv)
    full_cmd = "python run_today.py " + " ".join(shlex.quote(a) for a in eff_argv)

    run_id = new_id()
    db_path = ROOT / "data" / "db" / "web_intel.duckdb"
    db = WebIntelDB(db_path)
    try:
        db.create_crawl_run(
            run_id=run_id,
            input_path=str(args.input),
            strategy=args.strategy,
            limit_sources=args.profile_limit,
            max_articles_per_source=max_urls_eff,
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
                    "max_urls_resolved": max_urls_eff,
                    "step_timeout_seconds": args.step_timeout_seconds,
                    "close_spider_timeout": args.close_spider_timeout,
                    "force_refresh": bool(args.force_refresh),
                    "skip_profile": bool(args.skip_profile),
                    "include_gdelt": bool(args.include_gdelt),
                    "gdelt_query": args.gdelt_query,
                    "gdelt_max_records": args.gdelt_max_records,
                    "gdelt_extract_content": bool(args.gdelt_extract_content),
                    "include_apis": bool(args.include_apis),
                    "apis": args.apis,
                    "api_query": args.api_query,
                    "api_max_records": args.api_max_records,
                    "api_extract_content": bool(args.api_extract_content),
                    "raw_source_lines": raw_source_lines,
                },
                sort_keys=True,
            ),
            notes="run_today.py",
        )
    finally:
        db.close()

    _write_run_meta(
        run_id=run_id,
        argv_repr=["run_today.py", *eff_argv],
        full_cmd=full_cmd,
        extra={
            "raw_source_lines": raw_source_lines,
            "include_apis": bool(args.include_apis),
            "apis": args.apis,
        },
    )

    commands: list[list[str]] = []
    if args.include_apis:
        commands.append(
            build_api_hub_command(
                python_executable=sys.executable,
                date_arg=args.date,
                timezone_arg=args.timezone,
                apis=args.apis,
                api_query=args.api_query,
                api_max_records=args.api_max_records,
                api_extract_content=bool(args.api_extract_content),
            )
        )
    if args.include_gdelt:
        commands.append(
            build_gdelt_command(
                python_executable=sys.executable,
                date_arg=args.date,
                timezone_arg=args.timezone,
                query=args.gdelt_query,
                max_records=args.gdelt_max_records,
                extract_content=bool(args.gdelt_extract_content),
            )
        )
    commands.extend(
        build_today_commands(
            python_executable=sys.executable,
            input_path=args.input,
            profile_limit_cli=args.profile_limit,
            strategy=args.strategy,
            force_refresh=bool(args.force_refresh),
            run_id=run_id,
            date_arg=args.date,
            timezone_arg=args.timezone,
            max_urls_per_source_resolved=max_urls_eff,
            close_spider_timeout=args.close_spider_timeout,
            profile_concurrency=args.profile_concurrency,
            skip_profile=bool(args.skip_profile),
        )
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
