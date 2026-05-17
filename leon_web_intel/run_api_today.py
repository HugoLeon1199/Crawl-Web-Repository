#!/usr/bin/env python3
"""Unified public API collectors for the target calendar day (API Hub v1)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import httpx  # noqa: E402
from loguru import logger  # noqa: E402

from collectors.api_adapters.base import ApiAdapter, ApiRecord, authors_to_json  # noqa: E402
from collectors.api_adapters.registry import resolve_adapter_names  # noqa: E402
from extraction.article_extractor import compute_quality_score, extract_article  # noqa: E402
from reporting.api_hub_report import write_today_api_report  # noqa: E402
from settings import load_crawl_rules  # noqa: E402
from storage.db import WebIntelDB, new_id, utc_now  # noqa: E402
from storage.raw_store import RawStore  # noqa: E402
from utils.hashing import sha256_text  # noqa: E402
from utils.logging_config import configure_logging  # noqa: E402
from utils.today_filter import resolve_calendar_date, target_date_range  # noqa: E402


def intel_dedupe_key(url: str) -> str:
    return sha256_text(url.strip().split("#", 1)[0])


def api_record_to_row(
    rec: ApiRecord,
    *,
    target_calendar_date: str,
    timezone_name: str,
) -> dict[str, Any]:
    rid = sha256_text(f"{rec.api_name}|{rec.url.strip()}")
    raw_meta = json.dumps(rec.raw_metadata, ensure_ascii=False, default=str)
    content_hash = sha256_text(f"{rec.url}\n{rec.title or ''}")
    return {
        "id": rid,
        "api_name": rec.api_name,
        "source_id": rec.source_id,
        "record_type": rec.record_type,
        "title": rec.title,
        "url": rec.url,
        "published_at": rec.published_at,
        "updated_at": rec.updated_at,
        "summary": rec.summary,
        "content": rec.content,
        "language": rec.language,
        "domain": rec.domain,
        "country": rec.country,
        "authors_json": authors_to_json(rec.authors),
        "raw_metadata": raw_meta,
        "discovery_method": rec.discovery_method,
        "content_hash": content_hash,
        "collected_at": utc_now(),
        "target_calendar_date": target_calendar_date,
        "timezone_name": timezone_name,
    }


def discovered_row(rec: ApiRecord) -> dict[str, Any]:
    return {
        "id": new_id(),
        "source_id": rec.source_id,
        "url": rec.url,
        "discovery_method": f"api_hub:{rec.api_name}",
        "title": rec.title,
        "published_at": rec.published_at,
        "raw_metadata": json.dumps({"api_name": rec.api_name}, ensure_ascii=False),
        "discovered_at": utc_now(),
    }


def should_attempt_extract(url: str) -> bool:
    u = url.strip().lower()
    if not u.startswith("http"):
        return False
    if u.endswith(".pdf"):
        return False
    if "api.worldbank.org" in u:
        return False
    if "eutils.ncbi.nlm.nih.gov" in u:
        return False
    if "export.arxiv.org" in u:
        return False
    return True


def run_api_hub(
    *,
    db: WebIntelDB,
    rules,
    adapters: Sequence[ApiAdapter],
    target_date_str: str | None,
    timezone_name: str,
    query: str,
    max_records: int | None,
    extract_content: bool,
    continue_on_error: bool,
    clear_calendar_day: bool,
    raw_store: RawStore,
    client: httpx.Client,
) -> dict[str, Any]:
    target_cal = str(resolve_calendar_date(target_date_str, timezone_name))
    start_utc, end_utc = target_date_range(target_date_str, timezone_name)
    if clear_calendar_day:
        db.delete_api_records_for_calendar_day(target_calendar_date=target_cal, timezone_name=timezone_name)

    seen_keys: set[str] = set()
    counts: dict[str, int] = {}
    hash_set = db.fetch_distinct_content_hashes()

    for adapter in adapters:
        name = adapter.name
        try:
            records = adapter.collect_today(
                target_date_str=target_date_str,
                timezone_name=timezone_name,
                query=query,
                max_records=max_records,
                rules=rules,
                client=client,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("API hub adapter {} failed", name)
            db.insert_crawl_error(
                {
                    "id": new_id(),
                    "source_id": None,
                    "url": None,
                    "stage": f"api_hub:{name}",
                    "error_type": "ApiHubError",
                    "error_message": str(exc)[:2000],
                    "created_at": utc_now(),
                }
            )
            if not continue_on_error:
                raise
            continue

        for rec in records:
            dk = intel_dedupe_key(rec.url)
            if dk in seen_keys:
                continue
            seen_keys.add(dk)
            row = api_record_to_row(rec, target_calendar_date=target_cal, timezone_name=timezone_name)
            db.insert_api_record(row)
            try:
                db.insert_discovered_url(discovered_row(rec))
            except Exception as exc:  # noqa: BLE001
                logger.debug("discovered_urls insert skipped {}: {}", rec.url, exc)
            counts[name] = counts.get(name, 0) + 1

            if extract_content and should_attempt_extract(rec.url):
                try:
                    res = extract_article(
                        rec.url,
                        rec.source_id,
                        "api_trafilatura_extract",
                        rules=rules,
                        raw_store=raw_store,
                        client=client,
                    )
                    paywall_triplet = (res.paywall_detected, res.login_detected, res.captcha_detected)
                    q = compute_quality_score(
                        title=res.title or rec.title,
                        content_length=res.content_length,
                        published_at=res.published_at or rec.published_at,
                        source_active=True,
                        content_hash=res.content_hash,
                        url=rec.url,
                        strategy="api_trafilatura_extract",
                        raw_path=res.raw_path,
                        extract_ok=res.extract_ok,
                        paywall_triplet=paywall_triplet,
                        existing_hashes=hash_set,
                    )
                    if res.extract_ok and res.content_hash:
                        aid = new_id()
                        db.insert_article(
                            {
                                "id": aid,
                                "source_id": rec.source_id,
                                "url": rec.url,
                                "title": res.title or rec.title,
                                "published_at": res.published_at or rec.published_at,
                                "content": res.content,
                                "content_length": res.content_length,
                                "content_hash": res.content_hash,
                                "language": res.language,
                                "crawl_strategy_used": "api_trafilatura_extract",
                                "raw_path": res.raw_path,
                                "extracted_at": utc_now(),
                                "quality_score": float(q),
                            }
                        )
                        hash_set.add(res.content_hash)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("API extract failed {}: {}", rec.url, exc)
                    db.insert_crawl_error(
                        {
                            "id": new_id(),
                            "source_id": rec.source_id,
                            "url": rec.url,
                            "stage": f"api_hub:{name}",
                            "error_type": "ApiExtractError",
                            "error_message": str(exc)[:2000],
                            "created_at": utc_now(),
                        }
                    )

    api_stats = db.get_api_summary_stats(target_date_str=target_date_str, timezone_name=timezone_name)
    return {
        "target_calendar_date": target_cal,
        "window_start_utc": start_utc,
        "window_end_utc": end_utc,
        "counts_written_this_run": counts,
        "api_summary": api_stats,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Leon Web Intel — API Hub for target calendar day")
    parser.add_argument("--date", default="today")
    parser.add_argument("--timezone", default="Europe/Amsterdam", metavar="TZ")
    parser.add_argument("--apis", default="all", help='"all" or comma-separated adapter keys')
    parser.add_argument("--query", default="*")
    parser.add_argument("--max-records", type=int, default=0, help="0 = no cap per adapter where supported")
    parser.add_argument("--extract-content", action="store_true", default=False)
    parser.add_argument("--no-extract-content", action="store_false", dest="extract_content")
    parser.set_defaults(continue_on_error=True)
    parser.add_argument("--no-continue-on-error", action="store_false", dest="continue_on_error")
    parser.add_argument("--fail-fast", action="store_true", help="Abort on first adapter failure")
    parser.add_argument("--clear-calendar-day", action="store_true", default=True)
    parser.add_argument("--no-clear-calendar-day", action="store_false", dest="clear_calendar_day")
    args = parser.parse_args(argv)

    configure_logging(ROOT / "logs" / "app.log")
    rules = load_crawl_rules(ROOT / "config" / "crawl_rules.yaml")
    continue_on_error = bool(args.continue_on_error) and not bool(args.fail_fast)
    max_rc = None if args.max_records <= 0 else args.max_records

    try:
        adapters = resolve_adapter_names(args.apis)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2

    headers = {
        "User-Agent": rules.user_agent,
        "Accept": "application/json, application/xml, text/html;q=0.9,*/*;q=0.8",
    }
    tok = os.getenv("GITHUB_TOKEN")
    if tok:
        headers["Authorization"] = f"Bearer {tok}"

    mailto = os.getenv("OPENALEX_CONTACT_EMAIL")
    if mailto:
        headers["User-Agent"] = f"{rules.user_agent} mailto:{mailto}"

    client = httpx.Client(headers=headers, follow_redirects=True, timeout=float(rules.request_timeout_seconds))
    raw_store = RawStore(ROOT / "data" / "raw")
    db_path = ROOT / "data" / "db" / "web_intel.duckdb"
    db = WebIntelDB(db_path)
    exports = ROOT / "data" / "exports"
    exports.mkdir(parents=True, exist_ok=True)
    meta_csv = exports / "today_api_metadata.csv"
    report_md = exports / "today_api_report.md"

    try:
        summary = run_api_hub(
            db=db,
            rules=rules,
            adapters=adapters,
            target_date_str=args.date,
            timezone_name=args.timezone,
            query=args.query,
            max_records=max_rc,
            extract_content=bool(args.extract_content),
            continue_on_error=continue_on_error,
            clear_calendar_day=bool(args.clear_calendar_day),
            raw_store=raw_store,
            client=client,
        )
        db.export_today_api_metadata_csv(meta_csv, target_date_str=args.date, timezone_name=args.timezone)
        api_err = db.api_hub_errors_by_adapter(target_date_str=args.date, timezone_name=args.timezone)
        argv_eff = sys.argv if argv is None else ["run_api_today.py", *[str(a) for a in argv]]
        write_today_api_report(
            report_md,
            target_calendar_date=summary["target_calendar_date"],
            timezone_name=args.timezone,
            window_start_utc=summary["window_start_utc"],
            window_end_utc=summary["window_end_utc"],
            counts_by_adapter=summary["api_summary"]["records_by_adapter"],
            extracted_fulltext_n=int(summary["api_summary"]["api_extracted_fulltext"]),
            api_errors_by_adapter=api_err,
            argv=argv_eff,
        )
        print("")
        print("===== API HUB COMPLETE =====")
        print(f"Rows by adapter (window): {summary['api_summary']['records_by_adapter']}")
        print(meta_csv.resolve())
        print(report_md.resolve())
        return 0
    except Exception:
        logger.exception("API hub fatal")
        return 1
    finally:
        client.close()
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
