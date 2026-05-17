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
    """Markdown report for public-discovery \"today\" slice + GDELT + full-run meta."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    stats = db.get_today_summary_stats(target_date_str=target_date, timezone_name=timezone_name)
    target_cal = str(stats["target_date"])
    articles = stats["today_articles"]

    strat_counts = Counter(str(a.get("crawl_strategy_used") or "unknown") for a in articles)
    rss_n = int(strat_counts.get("rss_then_article_extract", 0))
    sm_n = int(strat_counts.get("sitemap_then_article_extract", 0))
    html_n = int(strat_counts.get("html_then_trafilatura", 0))
    gdelt_art_n = int(strat_counts.get("gdelt_then_article_extract", 0))

    gdelt_discovered = db.count_gdelt_doc_hits(target_calendar_date=target_cal, timezone_name=timezone_name)
    gdelt_extracted_window = db.count_gdelt_extracted_in_window(target_date_str=target_date, timezone_name=timezone_name)

    global_stats = db.get_crawl_summary_stats()
    profile_sources = int(global_stats.get("total_sources") or 0)

    err_win = stats.get("errors_by_type_window") or {}
    access_n = int(err_win.get("AccessControlDetected", 0))
    short_n = int(err_win.get("ShortContent", 0))
    not_today_err = int(stats.get("not_today_errors") or 0)

    sorted_arts = sorted(
        articles,
        key=lambda r: (float(r.get("quality_score") or 0), str(r.get("title") or "")),
        reverse=True,
    )[:50]

    meta_cmd = ""
    meta_rid = ""
    if run_meta_path and run_meta_path.is_file():
        try:
            meta = json.loads(run_meta_path.read_text(encoding="utf-8"))
            meta_cmd = str(meta.get("full_run_command") or meta.get("argv_join") or "").strip()
            meta_rid = str(meta.get("run_id") or "").strip()
        except (json.JSONDecodeError, OSError):
            meta_cmd = ""

    lines: list[str] = [
        "# Today Crawl Report",
        "",
        "## Target",
        f"- Calendar date: **{stats['target_date']}**",
        f"- Timezone: **{stats['timezone']}**",
        f"- UTC window: `{stats['window_start_utc']}` → `{stats['window_end_utc']}`",
        "",
        "## Totals",
        f"- **Sources profiled (global DB):** {profile_sources}",
        f"- **GDELT ArtList rows stored (this day+TZ):** {gdelt_discovered}",
        f"- **GDELT extracted articles (window by extracted_at):** {gdelt_extracted_window}",
        f"- **Today articles (RSS lane, export filter):** {rss_n}",
        f"- **Today articles (sitemap lane, export filter):** {sm_n}",
        f"- **Today articles (HTML lane, export filter):** {html_n}",
        f"- **Today articles (GDELT lane, export filter):** {gdelt_art_n}",
        f"- **Total today articles (export filter):** {stats['today_article_count']}",
        f"- Errors logged (UTC window): {stats['total_errors_window']}",
        f"- Frontier skipped **NotToday** (seen in window): {stats['not_today_skipped_frontier']}",
        f"- **NotToday** crawl_errors (window): {not_today_err}",
        f"- **AccessControlDetected** (window): {access_n}",
        f"- **ShortContent** (window): {short_n}",
        "",
        "## Errors By Type (window)",
        _fmt_dict_counts(err_win).rstrip(),
        "",
        "## Articles By Strategy (today export)",
        _fmt_dict_counts(dict(strat_counts)).rstrip(),
        "",
        "## Top Sources By Today Articles",
        _fmt_top_sources(stats.get("top_sources_today") or []).rstrip(),
        "",
        "## Top Articles (up to 50)",
        "| source_id | title | published_at | url | quality_score |",
        "|---|---|---|---|---|",
    ]
    for r in sorted_arts:
        title = str(r.get("title") or "").replace("|", "\\|").replace("\n", " ")[:200]
        lines.append(
            f"| {r.get('source_id') or ''} | {title} | {r.get('published_at') or ''} | {r.get('url') or ''} | {r.get('quality_score') or ''} |"
        )
    if not sorted_arts:
        lines.append("| — | — | — | — | — |")

    lines.extend(
        [
            "",
            "## Limitations",
            "- Public discovery only (GDELT DOC ArtList + RSS / sitemap `lastmod` / bounded homepage links); no paywall, login, CAPTCHA bypass.",
            "- GDELT: API caps 250 rows per request; tiling/bisection reduces truncation but extreme volumes may still be incomplete.",
            "- Some sites do not expose every same-day article in feeds or sitemap.",
            "- HTML discovery is bounded by depth and URL caps per source; not exhaustive site crawl.",
            "",
        ]
    )

    lines.extend(["## Full run command", ""])
    if meta_cmd:
        lines.append(f"- `{meta_cmd}`")
    else:
        lines.append("- *(No `today_run_meta.json` found — run `run_today.py` to record the command.)*")
    if meta_rid:
        lines.extend(["", "## Run ID", "", f"- `{meta_rid}`", ""])

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
