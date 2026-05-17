from __future__ import annotations

from pathlib import Path

import duckdb

from reporting.crawl_report import write_final_crawl_report
from run_pipeline import build_pipeline_commands
from storage.db import WebIntelDB


def test_crawl_runs_create_finish(tmp_path: Path) -> None:
    db_path = tmp_path / "web_intel.duckdb"
    db = WebIntelDB(db_path)
    try:
        db.create_crawl_run(
            run_id="run-1",
            input_path="config/sources_raw.txt",
            strategy="all",
            limit_sources=20,
            max_articles_per_source=3,
            force_refresh=True,
            config_json="{}",
        )
        db.finish_crawl_run(run_id="run-1", status="success", notes="ok")
    finally:
        db.close()

    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        row = conn.execute(
            "SELECT status, limit_sources, max_articles_per_source, notes FROM crawl_runs WHERE run_id = 'run-1'"
        ).fetchone()
    finally:
        conn.close()
    assert row == ("success", 20, 3, "ok")


def test_frontier_upsert_and_mark(tmp_path: Path) -> None:
    db = WebIntelDB(tmp_path / "web_intel.duckdb")
    try:
        db.upsert_frontier_url(
            source_id="s1",
            url="https://example.com/a",
            strategy="rss_then_article_extract",
        )
        assert db.fetch_frontier_summary()["pending"] == 1

        db.mark_frontier_crawled(url="https://example.com/a", content_hash="abc")
        summary = db.fetch_frontier_summary()
        assert summary["crawled"] == 1

        db.upsert_frontier_url(
            source_id="s1",
            url="https://example.com/b",
            strategy="rss_then_article_extract",
        )
        db.mark_frontier_failed(
            url="https://example.com/b",
            error_type="FetchError",
            error_message="boom",
        )
        summary = db.fetch_frontier_summary()
        assert summary["failed"] == 1
    finally:
        db.close()


def test_source_health_empty_db(tmp_path: Path) -> None:
    db = WebIntelDB(tmp_path / "web_intel.duckdb")
    try:
        db.update_source_health_from_current_db()
        stats = db.get_crawl_summary_stats()
        assert stats["total_sources"] == 0
        assert stats["total_articles"] == 0
        assert stats["total_errors"] == 0
    finally:
        db.close()


def test_export_empty_db_no_crash(tmp_path: Path) -> None:
    db = WebIntelDB(tmp_path / "web_intel.duckdb")
    out = tmp_path / "exports"
    try:
        db.export_articles_csv(out / "articles.csv")
        db.export_articles_parquet(out / "articles.parquet")
        db.export_crawl_errors_csv(out / "crawl_errors.csv")
        db.export_discovered_urls_csv(out / "discovered_urls.csv")
        db.export_crawl_frontier_csv(out / "crawl_frontier.csv")
        db.export_source_health_csv(out / "source_health.csv")
    finally:
        db.close()

    assert (out / "articles.csv").is_file()
    assert (out / "articles.parquet").is_file()
    assert (out / "crawl_errors.csv").is_file()
    assert (out / "discovered_urls.csv").is_file()
    assert (out / "crawl_frontier.csv").is_file()
    assert (out / "source_health.csv").is_file()


def test_final_crawl_report_empty_db(tmp_path: Path) -> None:
    db = WebIntelDB(tmp_path / "web_intel.duckdb")
    report = tmp_path / "exports" / "final_crawl_report.md"
    try:
        write_final_crawl_report(db, report)
    finally:
        db.close()

    text = report.read_text(encoding="utf-8")
    assert "# Final Crawl Report" in text
    assert "No crawl run recorded yet" in text
    assert "robots obey enabled" in text


def test_run_pipeline_command_building() -> None:
    commands = build_pipeline_commands(
        python_executable="python",
        input_path=Path("config/sources_raw.txt"),
        limit=20,
        max_articles_per_source=3,
        strategy="all",
        force_refresh=True,
        run_id="run-1",
    )

    assert commands[0] == [
        "python",
        "run_profile.py",
        "--input",
        "config\\sources_raw.txt" if "\\" in str(Path("config/sources_raw.txt")) else "config/sources_raw.txt",
        "--profile-only",
        "--limit",
        "20",
        "--force-refresh",
    ]
    assert commands[1][-2:] == ["--run-id", "run-1"]
    assert commands[1][0:2] == ["python", "run_scrapy.py"]
    assert commands[2] == ["python", "run_export.py"]
