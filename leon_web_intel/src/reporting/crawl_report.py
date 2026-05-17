"""Final crawl report writer."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from storage.db import WebIntelDB


def _fmt_dict_counts(values: dict[str, int]) -> str:
    if not values:
        return "- None\n"
    return "".join(f"- {key}: {value}\n" for key, value in values.items())


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
