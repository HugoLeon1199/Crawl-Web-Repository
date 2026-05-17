"""Final crawl report writer."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from storage.db import WebIntelDB


def write_today_crawl_report(
    db: WebIntelDB,
    out_path: Path,
    *,
    target_date: str | None,
    timezone_name: str,
    run_meta_path: Path | None = None,
) -> None:
    """Markdown report: Scrapy today slice + GDELT + API Hub + exports."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    stats = db.get_today_summary_stats(target_date_str=target_date, timezone_name=timezone_name)
    target_cal = str(stats["target_date"])
    articles = stats["today_articles"]

    strat_counts = Counter(str(a.get("crawl_strategy_used") or "unknown") for a in articles)
    rss_n = int(strat_counts.get("rss_then_article_extract", 0))
    sm_n = int(strat_counts.get("sitemap_then_article_extract", 0))
    html_n = int(strat_counts.get("html_then_trafilatura", 0))
    gdelt_art_n = int(strat_counts.get("gdelt_then_article_extract", 0))
    api_lane_n = int(strat_counts.get("api_trafilatura_extract", 0))

    gdelt_discovered = db.count_gdelt_doc_hits(target_calendar_date=target_cal, timezone_name=timezone_name)
    gdelt_extracted_window = db.count_gdelt_extracted_in_window(target_date_str=target_date, timezone_name=timezone_name)

    global_stats = db.get_crawl_summary_stats()
    profile_sources = int(global_stats.get("total_sources") or 0)

    api_summary = db.get_api_summary_stats(target_date_str=target_date, timezone_name=timezone_name)
    api_by_adapter: dict[str, int] = api_summary.get("records_by_adapter") or {}
    api_extracted = int(api_summary.get("api_extracted_fulltext") or 0)
    api_hub_err = db.api_hub_errors_by_adapter(target_date_str=target_date, timezone_name=timezone_name)

    err_win = stats.get("errors_by_type_window") or {}
    access_n = int(err_win.get("AccessControlDetected", 0))
    short_n = int(err_win.get("ShortContent", 0))
    not_today_err = int(stats.get("not_today_errors") or 0)
    dup_n = int(err_win.get("DuplicateContent", 0))

    sorted_arts = sorted(
        articles,
        key=lambda r: (float(r.get("quality_score") or 0), str(r.get("title") or "")),
        reverse=True,
    )

    api_headlines = db.fetch_today_api_headlines(target_date_str=target_date, timezone_name=timezone_name, limit=80)

    meta_cmd = ""
    meta_rid = ""
    meta_raw_lines = ""
    if run_meta_path and run_meta_path.is_file():
        try:
            meta = json.loads(run_meta_path.read_text(encoding="utf-8"))
            meta_cmd = str(meta.get("full_run_command") or meta.get("argv_join") or "").strip()
            meta_rid = str(meta.get("run_id") or "").strip()
            rsl = meta.get("raw_source_lines")
            meta_raw_lines = str(rsl) if rsl is not None else ""
        except (json.JSONDecodeError, OSError):
            meta_cmd = ""

    distinct_profiles_today = int(stats.get("distinct_article_sources_today") or 0)
    full_body_local = db.count_articles_with_body_in_window(target_date_str=target_date, timezone_name=timezone_name)
    intel_total = int(stats["today_article_count"]) + int(api_summary.get("total_api_records_window") or 0)

    adapter_keys = [
        "gdelt",
        "openalex",
        "arxiv",
        "sec",
        "world_bank",
        "pubmed",
        "github",
        "crossref",
        "semantic_scholar",
    ]

    seen_urls: set[str] = set()
    combined_top: list[tuple[str, str, str, str]] = []
    for r in sorted_arts:
        if len(combined_top) >= 50:
            break
        u = str(r.get("url") or "").strip()
        if not u or u in seen_urls:
            continue
        seen_urls.add(u)
        combined_top.append(
            (
                "scrapy",
                str(r.get("title") or ""),
                u,
                str(r.get("source_id") or ""),
            )
        )
    for h in api_headlines:
        if len(combined_top) >= 50:
            break
        u = str(h.get("url") or "").strip()
        if not u or u in seen_urls:
            continue
        seen_urls.add(u)
        combined_top.append(
            (
                "api",
                str(h.get("title") or ""),
                u,
                str(h.get("api_name") or ""),
            )
        )

    lines: list[str] = [
        "# Today Final Report",
        "",
        "## Target",
        f"- Calendar date: **{stats['target_date']}**",
        f"- Timezone: **{stats['timezone']}**",
        f"- UTC window: `{stats['window_start_utc']}` → `{stats['window_end_utc']}`",
        "",
        "## Sources",
        f"- **Raw source lines (input list, from last `run_today.py` meta):** {meta_raw_lines or '*(unknown — run `run_today.py` to record)*'}",
        f"- **Sources profiled (global DuckDB):** {profile_sources}",
        f"- **Distinct source_id in today articles (export window):** {distinct_profiles_today}",
        "",
        "## API Hub (metadata rows in UTC window)",
    ]
    for key in adapter_keys:
        lines.append(f"- **{key}:** {int(api_by_adapter.get(key, 0))}")
    lines.extend(
        [
            f"- **Total API metadata rows:** {int(api_summary.get('total_api_records_window') or 0)}",
            f"- **API full-text extracts (`api_trafilatura_extract`, window):** {api_extracted}",
            "",
            "## Scrapy / GDELT lanes (today export)",
            f"- **RSS articles:** {rss_n}",
            f"- **Sitemap articles:** {sm_n}",
            f"- **HTML articles:** {html_n}",
            f"- **GDELT-linked articles (strategy gdelt_then_article_extract):** {gdelt_art_n}",
            f"- **API-linked full-text articles (strategy api_trafilatura_extract):** {api_lane_n}",
            f"- **GDELT ArtList rows stored (calendar day + TZ):** {gdelt_discovered}",
            f"- **GDELT extracts (window by extracted_at):** {gdelt_extracted_window}",
            f"- **Total today articles (export filter):** {stats['today_article_count']}",
            "",
            "## Intelligence totals",
            f"- **Total today intelligence items (articles + API rows; URLs may overlap across lanes):** {intel_total}",
            f"- **Articles with substantive body text locally (length > 200, window):** {full_body_local}",
            "",
            "## Errors",
            f"- **Total errors (window):** {stats['total_errors_window']}",
            "",
            "### Errors by type (window)",
            _fmt_dict_counts(err_win).rstrip(),
            "",
            "### API Hub errors by adapter",
            _fmt_dict_counts({k: int(v) for k, v in api_hub_err.items()}).rstrip()
            if api_hub_err
            else "- None\n",
            "",
            "### Selected crawl signals",
            f"- **AccessControlDetected:** {access_n}",
            f"- **ShortContent:** {short_n}",
            f"- **NotToday (crawl_errors):** {not_today_err}",
            f"- **DuplicateContent:** {dup_n}",
            f"- **Frontier skipped NotToday:** {stats['not_today_skipped_frontier']}",
            "",
            "## Articles by strategy (today export)",
            _fmt_dict_counts(dict(strat_counts)).rstrip(),
            "",
            "## Top sources by today articles",
            _fmt_top_sources(stats.get("top_sources_today") or []).rstrip(),
            "",
            "## Top APIs by record count",
            _fmt_dict_counts(dict(sorted(api_by_adapter.items(), key=lambda kv: (-kv[1], kv[0])))).rstrip()
            if api_by_adapter
            else "- None\n",
            "",
            "## Top titles / URLs (mixed API + Scrapy, up to 50, URL-deduplicated)",
            "| kind | title | url | detail |",
            "|---|---|---|---|",
        ]
    )
    for kind, title, url, detail in combined_top:
        t_esc = title.replace("|", "\\|").replace("\n", " ")[:200]
        lines.append(f"| {kind} | {t_esc} | {url} | {str(detail).replace('|', '\\|')[:120]} |")
    if not combined_top:
        lines.append("| — | — | — | — |")

    lines.extend(
        [
            "",
            "## Output files (today slice)",
            "- `data/exports/today_final_report.md` (this file)",
            "- `data/exports/today_articles_metadata.csv`",
            "- `data/exports/today_api_metadata.csv`",
            "- `data/exports/today_api_report.md`",
            "- `data/exports/today_ai_input.jsonl` *(full text — keep local; do not commit if policy forbids)*",
            "- `data/exports/today_gdelt_metadata.csv` / `today_gdelt_report.md` *(when GDELT lane ran)*",
            "- `data/exports/today_crawl_errors.csv`",
            "",
            "## Full command",
            "",
        ]
    )
    if meta_cmd:
        lines.append(f"- `{meta_cmd}`")
    else:
        lines.append("- *(No `today_run_meta.json` found — run `run_today.py` to record the command.)*")
    if meta_rid:
        lines.extend(["", "## Run ID", "", f"- `{meta_rid}`", ""])

    lines.extend(
        [
            "",
            "## Split runs (if full orchestration times out)",
            "- `python run_api_today.py --date today --timezone Europe/Amsterdam --apis all --query \"*\" --max-records 0 --extract-content`",
            "- `python run_today.py --strategy rss --skip-profile ...`",
            "- `python run_today.py --strategy sitemap --skip-profile ...`",
            "- `python run_today.py --strategy html --skip-profile ...`",
            "- `python run_export.py --today-only --date today --timezone Europe/Amsterdam`",
            "",
            "## Limitations",
            "- Public HTTP/API endpoints only: no paywall, login, CAPTCHA bypass; no proxies or stealth.",
            "- API Hub respects upstream rate limits with bounded retries; some adapters may return partial results when throttled.",
            "- GDELT ArtList is capped per request; tiling reduces loss but extreme volumes may still be incomplete.",
            "- Scrapy lanes remain bounded by per-source URL caps and profiler strategies.",
            "- `today_ai_input.jsonl` may contain full article bodies — treat as local-only intelligence corpora.",
            "",
        ]
    )

    out_path.write_text("\n".join(lines), encoding="utf-8")


def _fmt_dict_counts(values: dict[str, int]) -> str:
    if not values:
        return "- None\n"
    return "".join(f"- {key}: {value}\n" for key, value in sorted(values.items(), key=lambda kv: (-kv[1], kv[0])))


def _fmt_top_sources(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "- None\n"
    return "".join(f"- {row['source_id']}: {row['count']}\n" for row in rows)


def _latest_run(db: WebIntelDB) -> dict[str, Any] | None:
    with db._lock:  # noqa: SLF001 - report is a local DB companion.
        df = db.conn.execute(
            """
            SELECT *
            FROM crawl_runs
            ORDER BY started_at DESC
            LIMIT 1
            """
        ).fetchdf()
    if df.empty:
        return None
    return df.iloc[0].to_dict()


def write_final_crawl_report(db: WebIntelDB, out_path: Path) -> None:
    """Write an end-to-end crawl report. Safe for empty freshly-created DBs."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    stats = db.get_crawl_summary_stats()
    frontier = db.fetch_frontier_summary()
    latest = _latest_run(db)
    content_len = stats["content_length"]

    lines: list[str] = [
        "# Final Crawl Report",
        "",
        "## Run Summary",
    ]
    if latest:
        lines.extend(
            [
                f"- Run ID: {latest.get('run_id') or ''}",
                f"- Status: {latest.get('status') or ''}",
                f"- Started at: {latest.get('started_at') or ''}",
                f"- Ended at: {latest.get('ended_at') or ''}",
                f"- Input path: {latest.get('input_path') or ''}",
                f"- Strategy: {latest.get('strategy') or ''}",
                f"- Limit sources: {latest.get('limit_sources') or ''}",
                f"- Max articles per source: {latest.get('max_articles_per_source') or ''}",
                f"- Force refresh: {latest.get('force_refresh')}",
            ]
        )
    else:
        lines.append("- No crawl run recorded yet.")

    lines.extend(
        [
            "",
            "## Totals",
            f"- Sources: {stats['total_sources']}",
            f"- Discovered URLs: {stats['total_discovered_urls']}",
            f"- Frontier pending: {frontier.get('pending', 0)}",
            f"- Frontier crawling: {frontier.get('crawling', 0)}",
            f"- Frontier crawled: {frontier.get('crawled', 0)}",
            f"- Frontier failed: {frontier.get('failed', 0)}",
            f"- Frontier skipped: {frontier.get('skipped', 0)}",
            f"- Articles: {stats['total_articles']}",
            f"- Errors: {stats['total_errors']}",
            "",
            "## Articles By Strategy",
            _fmt_dict_counts(stats["articles_by_strategy"]).rstrip(),
            "",
            "## Errors By Type",
            _fmt_dict_counts(stats["errors_by_type"]).rstrip(),
            "",
            "## Top Sources By Articles",
            _fmt_top_sources(stats["top_sources_by_articles"]).rstrip(),
            "",
            "## Top Sources By Errors",
            _fmt_top_sources(stats["top_sources_by_errors"]).rstrip(),
            "",
            "## Quality And Content",
            f"- Average quality_score: {stats['avg_quality_score']:.4f}",
            f"- Content length min: {content_len['min']}",
            f"- Content length avg: {content_len['avg']:.2f}",
            f"- Content length max: {content_len['max']}",
            "",
            "## Safety Notes",
            "- robots obey enabled",
            "- no captcha bypass",
            "- no login automation",
            "- no paywall bypass",
            "- Playwright not part of Scrapy production path in this phase",
            "",
            "## Limitations",
            "- local DuckDB",
            "- bounded Scrapy crawl",
            "- no distributed scheduler yet",
            "",
        ]
    )
    out_path.write_text("\n".join(lines), encoding="utf-8")
