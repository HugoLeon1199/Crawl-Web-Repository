#!/usr/bin/env python3
"""Fetch GDELT DOC ArtList for the target calendar day and optionally extract articles."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from collectors.gdelt_collector import iter_gdelt_artlist_day, url_to_gdelt_source_id  # noqa: E402
from extraction.article_extractor import compute_quality_score, extract_article  # noqa: E402
from loguru import logger  # noqa: E402
from reporting.gdelt_report import write_today_gdelt_report  # noqa: E402
from settings import load_crawl_rules  # noqa: E402
from storage.db import WebIntelDB, new_id, utc_now  # noqa: E402
from storage.raw_store import RawStore  # noqa: E402
from utils.logging_config import configure_logging  # noqa: E402
from utils.today_filter import resolve_calendar_date, target_date_range  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Leon Web Intel — GDELT DOC ArtList for target day")
    parser.add_argument("--date", default="today", help='YYYY-MM-DD or "today"')
    parser.add_argument("--timezone", default="Europe/Amsterdam", metavar="TZ")
    parser.add_argument("--query", default="*", help='GDELT query (* → broad predicate)')
    parser.add_argument(
        "--max-records",
        type=int,
        default=0,
        help="Cap unique URLs (0 = no cap; API still max 250 per request)",
    )
    parser.add_argument("--extract-content", action="store_true", help="Fetch URL + trafilatura → articles table")
    parser.add_argument(
        "--clear-day",
        action="store_true",
        default=True,
        help="Remove prior gdelt_doc_hits rows for this calendar day+timezone (default: on)",
    )
    parser.add_argument("--no-clear-day", action="store_false", dest="clear_day")
    args = parser.parse_args(argv)

    exports = ROOT / "data" / "exports"
    exports.mkdir(parents=True, exist_ok=True)
    log_path = ROOT / "logs" / "app.log"
    configure_logging(log_path)

    rules = load_crawl_rules(ROOT / "config" / "crawl_rules.yaml")
    target_cal = str(resolve_calendar_date(args.date, args.timezone))
    start_utc, end_utc = target_date_range(args.date, args.timezone)
    cap = None if args.max_records <= 0 else args.max_records

    db_path = ROOT / "data" / "db" / "web_intel.duckdb"
    db = WebIntelDB(db_path)
    raw_store = RawStore(ROOT / "data" / "raw")
    meta_csv = ROOT / "data" / "exports" / "today_gdelt_metadata.csv"
    report_md = ROOT / "data" / "exports" / "today_gdelt_report.md"

    extracted_ok = 0
    extract_errors = 0

    try:
        if args.clear_day:
            db.delete_gdelt_doc_hits_for_day(target_calendar_date=target_cal, timezone_name=args.timezone)

        hash_set = db.fetch_distinct_content_hashes()

        import httpx

        extract_client = httpx.Client(
            headers={"User-Agent": rules.user_agent},
            follow_redirects=True,
            timeout=float(rules.request_timeout_seconds),
        )

        for art in iter_gdelt_artlist_day(
            query=args.query,
            window_start_utc=start_utc,
            window_end_utc=end_utc,
            max_records_total=cap,
            http_timeout=float(rules.request_timeout_seconds) + 30.0,
        ):
            url = str(art.get("url") or "").strip()
            if not url.startswith("http"):
                continue
            hit_id = new_id()
            domain = str(art.get("domain") or "").strip()
            title = str(art.get("title") or "").strip() or None
            seendate = str(art.get("seendate") or art.get("seenDate") or "").strip() or None
            row = {
                "id": hit_id,
                "target_calendar_date": target_cal,
                "timezone_name": args.timezone,
                "url": url,
                "title": title,
                "seendate": seendate,
                "domain": domain or None,
                "api_query": args.query,
                "window_start_utc": start_utc,
                "window_end_utc": end_utc,
                "fetched_at": utc_now(),
                "article_id": None,
                "extract_error": None,
            }
            db.insert_gdelt_doc_hit(row)

            if not args.extract_content:
                continue

            sid = url_to_gdelt_source_id(url)
            try:
                res = extract_article(
                    url,
                    sid,
                    "gdelt_then_article_extract",
                    rules=rules,
                    raw_store=raw_store,
                    client=extract_client,
                )
                paywall_triplet = (res.paywall_detected, res.login_detected, res.captcha_detected)
                q = compute_quality_score(
                    title=res.title or title,
                    content_length=res.content_length,
                    published_at=res.published_at or seendate,
                    source_active=True,
                    content_hash=res.content_hash,
                    url=url,
                    strategy="gdelt_then_article_extract",
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
                            "source_id": sid,
                            "url": url,
                            "title": res.title or title,
                            "published_at": res.published_at or seendate,
                            "content": res.content,
                            "content_length": res.content_length,
                            "content_hash": res.content_hash,
                            "language": res.language,
                            "crawl_strategy_used": "gdelt_then_article_extract",
                            "raw_path": res.raw_path,
                            "extracted_at": utc_now(),
                            "quality_score": float(q),
                        }
                    )
                    hash_set.add(res.content_hash)
                    db.update_gdelt_doc_hit_extract(hit_id, article_id=aid, extract_error=None)
                    extracted_ok += 1
                else:
                    err = "extract_ok=False or empty hash"
                    db.update_gdelt_doc_hit_extract(hit_id, article_id=None, extract_error=err)
                    extract_errors += 1
            except Exception as exc:  # noqa: BLE001
                logger.exception("GDELT extract failed {}", url)
                db.update_gdelt_doc_hit_extract(hit_id, article_id=None, extract_error=str(exc)[:2000])
                extract_errors += 1

        extract_client.close()

        total_hits = db.count_gdelt_doc_hits(target_calendar_date=target_cal, timezone_name=args.timezone)
        db.export_gdelt_doc_hits_csv(meta_csv, target_calendar_date=target_cal, timezone_name=args.timezone)
        write_today_gdelt_report(
            report_md,
            target_calendar_date=target_cal,
            timezone_name=args.timezone,
            utc_window=(start_utc, end_utc),
            query=args.query,
            total_hits=total_hits,
            extracted_ok=extracted_ok,
            extract_errors=extract_errors,
            argv=sys.argv,
        )
        print("")
        print("===== GDELT TODAY COMPLETE =====")
        print(f"Hits recorded: {total_hits}")
        print(f"Extracted articles: {extracted_ok}")
        print(f"Extract failures: {extract_errors}")
        print(meta_csv.resolve())
        print(report_md.resolve())
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
