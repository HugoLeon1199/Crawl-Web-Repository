"""DuckDB persistence."""

from __future__ import annotations

import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb

from utils.hashing import sha256_text


DDL = """
CREATE TABLE IF NOT EXISTS source_profiles (
  source_id TEXT PRIMARY KEY,
  input_url TEXT,
  normalized_url TEXT,
  domain TEXT,
  scheme TEXT,
  homepage_url TEXT,
  robots_url TEXT,
  robots_ok BOOLEAN,
  robots_sitemaps TEXT,
  robots_disallow_detected BOOLEAN,
  robots_can_fetch_homepage BOOLEAN,
  has_known_api BOOLEAN,
  known_api_adapter TEXT,
  known_api_endpoint_hint TEXT,
  has_rss BOOLEAN,
  rss_urls TEXT,
  rss_valid_count INTEGER,
  has_sitemap BOOLEAN,
  sitemap_urls TEXT,
  sitemap_url_count INTEGER,
  html_status_code INTEGER,
  html_title TEXT,
  html_text_length INTEGER,
  html_link_count INTEGER,
  html_extract_ok BOOLEAN,
  sample_extracted_text_length INTEGER,
  js_required BOOLEAN,
  paywall_detected BOOLEAN,
  captcha_detected BOOLEAN,
  login_detected BOOLEAN,
  best_strategy TEXT,
  tos_risk TEXT,
  status TEXT,
  error_message TEXT,
  profiled_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS discovered_urls (
  id TEXT PRIMARY KEY,
  source_id TEXT,
  url TEXT,
  discovery_method TEXT,
  title TEXT,
  published_at TEXT,
  raw_metadata TEXT,
  discovered_at TIMESTAMP,
  url_hash TEXT
);

CREATE TABLE IF NOT EXISTS articles (
  id TEXT PRIMARY KEY,
  source_id TEXT,
  url TEXT,
  title TEXT,
  published_at TEXT,
  content TEXT,
  content_length INTEGER,
  content_hash TEXT,
  language TEXT,
  crawl_strategy_used TEXT,
  raw_path TEXT,
  extracted_at TIMESTAMP,
  quality_score DOUBLE
);

CREATE TABLE IF NOT EXISTS crawl_errors (
  id TEXT PRIMARY KEY,
  source_id TEXT,
  url TEXT,
  stage TEXT,
  error_type TEXT,
  error_message TEXT,
  created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS crawl_runs (
  run_id TEXT PRIMARY KEY,
  started_at TIMESTAMP,
  ended_at TIMESTAMP,
  status TEXT,
  input_path TEXT,
  strategy TEXT,
  limit_sources INTEGER,
  max_articles_per_source INTEGER,
  force_refresh BOOLEAN,
  config_json TEXT,
  total_sources INTEGER,
  total_discovered_urls INTEGER,
  total_articles INTEGER,
  total_errors INTEGER,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS crawl_frontier (
  url_hash TEXT PRIMARY KEY,
  source_id TEXT,
  url TEXT,
  strategy TEXT,
  status TEXT,
  priority INTEGER,
  retry_count INTEGER,
  last_error_type TEXT,
  last_error_message TEXT,
  first_seen_at TIMESTAMP,
  last_seen_at TIMESTAMP,
  last_crawled_at TIMESTAMP,
  next_crawl_at TIMESTAMP,
  content_hash TEXT
);

CREATE TABLE IF NOT EXISTS source_health (
  source_id TEXT PRIMARY KEY,
  total_urls_seen INTEGER,
  total_articles_inserted INTEGER,
  total_errors INTEGER,
  last_success_at TIMESTAMP,
  last_error_at TIMESTAMP,
  last_error_type TEXT,
  success_rate DOUBLE,
  updated_at TIMESTAMP
);
"""


class WebIntelDB:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.conn = duckdb.connect(str(db_path))
        self.conn.execute(DDL)
        self._run_migrations()

    def _safe_add_column(self, table: str, column: str, definition: str) -> None:
        try:
            cols = {
                row[1]
                for row in self.conn.execute(f"PRAGMA table_info('{table}')").fetchall()
            }
            if column in cols:
                return
            self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        except Exception:
            # DuckDB leaves the transaction aborted if ALTER fails.
            try:
                self.conn.execute("ROLLBACK")
            except Exception:
                pass

    def _run_migrations(self) -> None:
        """Add robots_can_fetch_homepage for DBs created before this column existed."""
        self._safe_add_column("source_profiles", "robots_can_fetch_homepage", "BOOLEAN DEFAULT TRUE")
        self._safe_add_column("discovered_urls", "url_hash", "TEXT")

    def close(self) -> None:
        with self._lock:
            self.conn.close()

    def upsert_source_profile(self, row: dict[str, Any]) -> None:
        with self._lock:
            sid = row["source_id"]
            self.conn.execute("DELETE FROM source_profiles WHERE source_id = ?", [sid])
            cols = ", ".join(row.keys())
            placeholders = ", ".join(["?" for _ in row])
            sql = f"INSERT INTO source_profiles ({cols}) VALUES ({placeholders})"
            self.conn.execute(sql, list(row.values()))

    def get_profile(self, source_id: str) -> dict[str, Any] | None:
        with self._lock:
            df = self.conn.execute(
                "SELECT * FROM source_profiles WHERE source_id = ?",
                [source_id],
            ).fetchdf()
            if df.empty:
                return None
            return df.iloc[0].to_dict()

    def fetch_all_profiles(self) -> list[dict[str, Any]]:
        with self._lock:
            df = self.conn.execute("SELECT * FROM source_profiles ORDER BY source_id").fetchdf()
            return df.to_dict("records")

    def insert_discovered_url(self, row: dict[str, Any]) -> None:
        with self._lock:
            if row.get("url") and not row.get("url_hash"):
                row = {**row, "url_hash": sha256_text(str(row["url"]))}
            cols = ", ".join(row.keys())
            placeholders = ", ".join(["?" for _ in row])
            sql = f"INSERT OR REPLACE INTO discovered_urls ({cols}) VALUES ({placeholders})"
            self.conn.execute(sql, list(row.values()))

    def insert_article(self, row: dict[str, Any]) -> None:
        with self._lock:
            cols = ", ".join(row.keys())
            placeholders = ", ".join(["?" for _ in row])
            sql = f"INSERT OR REPLACE INTO articles ({cols}) VALUES ({placeholders})"
            self.conn.execute(sql, list(row.values()))

    def insert_crawl_error(self, row: dict[str, Any]) -> None:
        with self._lock:
            cols = ", ".join(row.keys())
            placeholders = ", ".join(["?" for _ in row])
            sql = f"INSERT INTO crawl_errors ({cols}) VALUES ({placeholders})"
            self.conn.execute(sql, list(row.values()))

    def fetch_distinct_content_hashes(self) -> set[str]:
        with self._lock:
            try:
                res = self.conn.execute(
                    "SELECT DISTINCT content_hash FROM articles WHERE content_hash IS NOT NULL AND content_hash <> ''"
                ).fetchall()
                return {r[0] for r in res}
            except Exception:
                return set()

    def create_crawl_run(
        self,
        *,
        run_id: str,
        input_path: str,
        strategy: str,
        limit_sources: int | None,
        max_articles_per_source: int | None,
        force_refresh: bool,
        config_json: str = "",
        notes: str = "",
    ) -> None:
        with self._lock:
            self.conn.execute(
                """
                INSERT OR REPLACE INTO crawl_runs (
                  run_id, started_at, ended_at, status, input_path, strategy,
                  limit_sources, max_articles_per_source, force_refresh, config_json,
                  total_sources, total_discovered_urls, total_articles, total_errors, notes
                ) VALUES (?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0, 0, ?)
                """,
                [
                    run_id,
                    utc_now(),
                    "running",
                    input_path,
                    strategy,
                    limit_sources,
                    max_articles_per_source,
                    force_refresh,
                    config_json,
                    notes,
                ],
            )

    def finish_crawl_run(self, *, run_id: str, status: str, notes: str = "") -> None:
        stats = self.get_crawl_summary_stats()
        with self._lock:
            self.conn.execute(
                """
                UPDATE crawl_runs
                SET ended_at = ?,
                    status = ?,
                    total_sources = ?,
                    total_discovered_urls = ?,
                    total_articles = ?,
                    total_errors = ?,
                    notes = CASE WHEN ? <> '' THEN ? ELSE notes END
                WHERE run_id = ?
                """,
                [
                    utc_now(),
                    status,
                    stats["total_sources"],
                    stats["total_discovered_urls"],
                    stats["total_articles"],
                    stats["total_errors"],
                    notes,
                    notes,
                    run_id,
                ],
            )

    def upsert_frontier_url(
        self,
        *,
        source_id: str,
        url: str,
        strategy: str,
        status: str = "pending",
        priority: int = 100,
        next_crawl_at: datetime | None = None,
        content_hash: str | None = None,
    ) -> str:
        url_hash = sha256_text(url)
        now = utc_now()
        with self._lock:
            existing = self.conn.execute(
                "SELECT retry_count, first_seen_at FROM crawl_frontier WHERE url_hash = ?",
                [url_hash],
            ).fetchone()
            if existing:
                self.conn.execute(
                    """
                    UPDATE crawl_frontier
                    SET source_id = ?,
                        url = ?,
                        strategy = ?,
                        status = ?,
                        priority = ?,
                        last_seen_at = ?,
                        next_crawl_at = COALESCE(?, next_crawl_at),
                        content_hash = COALESCE(?, content_hash)
                    WHERE url_hash = ?
                    """,
                    [source_id, url, strategy, status, priority, now, next_crawl_at, content_hash, url_hash],
                )
            else:
                self.conn.execute(
                    """
                    INSERT INTO crawl_frontier (
                      url_hash, source_id, url, strategy, status, priority, retry_count,
                      last_error_type, last_error_message, first_seen_at, last_seen_at,
                      last_crawled_at, next_crawl_at, content_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, 0, NULL, NULL, ?, ?, NULL, ?, ?)
                    """,
                    [url_hash, source_id, url, strategy, status, priority, now, now, next_crawl_at, content_hash],
                )
        return url_hash

    def mark_frontier_crawled(self, *, url: str, content_hash: str | None = None) -> None:
        url_hash = sha256_text(url)
        with self._lock:
            self.conn.execute(
                """
                UPDATE crawl_frontier
                SET status = 'crawled',
                    last_crawled_at = ?,
                    last_seen_at = ?,
                    last_error_type = NULL,
                    last_error_message = NULL,
                    content_hash = COALESCE(?, content_hash)
                WHERE url_hash = ?
                """,
                [utc_now(), utc_now(), content_hash, url_hash],
            )

    def mark_frontier_failed(
        self,
        *,
        url: str,
        error_type: str,
        error_message: str,
        status: str = "failed",
    ) -> None:
        url_hash = sha256_text(url)
        with self._lock:
            self.conn.execute(
                """
                UPDATE crawl_frontier
                SET status = ?,
                    retry_count = COALESCE(retry_count, 0) + 1,
                    last_error_type = ?,
                    last_error_message = ?,
                    last_seen_at = ?,
                    next_crawl_at = NULL
                WHERE url_hash = ?
                """,
                [status, error_type, error_message[:2000], utc_now(), url_hash],
            )

    def mark_frontier_skipped(self, *, url: str, reason_type: str, reason_message: str = "") -> None:
        self.mark_frontier_failed(
            url=url,
            error_type=reason_type,
            error_message=reason_message,
            status="skipped",
        )

    def fetch_frontier_summary(self) -> dict[str, int]:
        with self._lock:
            rows = self.conn.execute(
                "SELECT status, COUNT(*) FROM crawl_frontier GROUP BY status"
            ).fetchall()
            out = {"pending": 0, "crawling": 0, "crawled": 0, "failed": 0, "skipped": 0}
            for status, count in rows:
                out[str(status or "pending")] = int(count or 0)
            return out

    def update_source_health_from_current_db(self) -> None:
        with self._lock:
            source_rows = self.conn.execute(
                """
                SELECT source_id FROM source_profiles
                UNION
                SELECT source_id FROM articles WHERE source_id IS NOT NULL AND source_id <> ''
                UNION
                SELECT source_id FROM crawl_errors WHERE source_id IS NOT NULL AND source_id <> ''
                UNION
                SELECT source_id FROM crawl_frontier WHERE source_id IS NOT NULL AND source_id <> ''
                """
            ).fetchall()
            now = utc_now()
            for (source_id,) in source_rows:
                total_urls_seen = self.conn.execute(
                    """
                    SELECT COUNT(DISTINCT url) FROM (
                      SELECT url FROM crawl_frontier WHERE source_id = ?
                      UNION
                      SELECT url FROM discovered_urls WHERE source_id = ?
                    )
                    """,
                    [source_id, source_id],
                ).fetchone()[0]
                total_articles = self.conn.execute(
                    "SELECT COUNT(*) FROM articles WHERE source_id = ?",
                    [source_id],
                ).fetchone()[0]
                total_errors = self.conn.execute(
                    "SELECT COUNT(*) FROM crawl_errors WHERE source_id = ?",
                    [source_id],
                ).fetchone()[0]
                last_success_at = self.conn.execute(
                    "SELECT MAX(extracted_at) FROM articles WHERE source_id = ?",
                    [source_id],
                ).fetchone()[0]
                last_error_at = self.conn.execute(
                    "SELECT MAX(created_at) FROM crawl_errors WHERE source_id = ?",
                    [source_id],
                ).fetchone()[0]
                last_error_type_row = self.conn.execute(
                    """
                    SELECT error_type FROM crawl_errors
                    WHERE source_id = ?
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    [source_id],
                ).fetchone()
                denom = int(total_articles or 0) + int(total_errors or 0)
                success_rate = float(total_articles or 0) / denom if denom else 0.0
                self.conn.execute(
                    """
                    INSERT OR REPLACE INTO source_health (
                      source_id, total_urls_seen, total_articles_inserted, total_errors,
                      last_success_at, last_error_at, last_error_type, success_rate, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        source_id,
                        int(total_urls_seen or 0),
                        int(total_articles or 0),
                        int(total_errors or 0),
                        last_success_at,
                        last_error_at,
                        last_error_type_row[0] if last_error_type_row else None,
                        success_rate,
                        now,
                    ],
                )

    def _export_query_csv(self, sql: str, out_path: Path) -> None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df = self.conn.execute(sql).fetchdf()
        df.to_csv(out_path, index=False)

    def export_articles_csv(self, out_path: Path) -> None:
        with self._lock:
            self._export_query_csv("SELECT * FROM articles ORDER BY extracted_at, id", out_path)

    def export_articles_parquet(self, out_path: Path) -> None:
        with self._lock:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            df = self.conn.execute("SELECT * FROM articles ORDER BY extracted_at, id").fetchdf()
            df.to_parquet(out_path, index=False)

    def export_crawl_errors_csv(self, out_path: Path) -> None:
        with self._lock:
            self._export_query_csv("SELECT * FROM crawl_errors ORDER BY created_at, id", out_path)

    def export_discovered_urls_csv(self, out_path: Path) -> None:
        with self._lock:
            self._export_query_csv("SELECT * FROM discovered_urls ORDER BY discovered_at, id", out_path)

    def export_crawl_frontier_csv(self, out_path: Path) -> None:
        with self._lock:
            self._export_query_csv("SELECT * FROM crawl_frontier ORDER BY last_seen_at, url_hash", out_path)

    def export_source_health_csv(self, out_path: Path) -> None:
        with self._lock:
            self._export_query_csv("SELECT * FROM source_health ORDER BY source_id", out_path)

    def get_crawl_summary_stats(self) -> dict[str, Any]:
        with self._lock:
            scalar_queries = {
                "total_sources": "SELECT COUNT(*) FROM source_profiles",
                "total_discovered_urls": "SELECT COUNT(*) FROM discovered_urls",
                "total_articles": "SELECT COUNT(*) FROM articles",
                "total_errors": "SELECT COUNT(*) FROM crawl_errors",
                "avg_quality_score": "SELECT AVG(quality_score) FROM articles",
            }
            stats: dict[str, Any] = {}
            for key, sql in scalar_queries.items():
                val = self.conn.execute(sql).fetchone()[0]
                if key == "avg_quality_score":
                    stats[key] = float(val) if val is not None else 0.0
                else:
                    stats[key] = int(val or 0)

            frontier = self.fetch_frontier_summary()
            stats["total_frontier_pending"] = frontier.get("pending", 0)
            stats["total_frontier_crawled"] = frontier.get("crawled", 0)
            stats["total_frontier_failed"] = frontier.get("failed", 0)
            stats["total_frontier_skipped"] = frontier.get("skipped", 0)

            stats["articles_by_strategy"] = {
                str(k or "unknown"): int(v or 0)
                for k, v in self.conn.execute(
                    "SELECT crawl_strategy_used, COUNT(*) FROM articles GROUP BY crawl_strategy_used ORDER BY COUNT(*) DESC"
                ).fetchall()
            }
            stats["errors_by_type"] = {
                str(k or "unknown"): int(v or 0)
                for k, v in self.conn.execute(
                    "SELECT error_type, COUNT(*) FROM crawl_errors GROUP BY error_type ORDER BY COUNT(*) DESC"
                ).fetchall()
            }
            stats["top_sources_by_articles"] = [
                {"source_id": str(source_id), "count": int(count or 0)}
                for source_id, count in self.conn.execute(
                    """
                    SELECT source_id, COUNT(*) AS n
                    FROM articles
                    GROUP BY source_id
                    ORDER BY n DESC, source_id
                    LIMIT 10
                    """
                ).fetchall()
            ]
            stats["top_sources_by_errors"] = [
                {"source_id": str(source_id), "count": int(count or 0)}
                for source_id, count in self.conn.execute(
                    """
                    SELECT source_id, COUNT(*) AS n
                    FROM crawl_errors
                    GROUP BY source_id
                    ORDER BY n DESC, source_id
                    LIMIT 10
                    """
                ).fetchall()
            ]
            min_len, avg_len, max_len = self.conn.execute(
                "SELECT MIN(content_length), AVG(content_length), MAX(content_length) FROM articles"
            ).fetchone()
            stats["content_length"] = {
                "min": int(min_len or 0),
                "avg": float(avg_len) if avg_len is not None else 0.0,
                "max": int(max_len or 0),
            }
            return stats

    def export_source_profiles_csv(self, out_path: Path) -> None:
        with self._lock:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            df = self.conn.execute("SELECT * FROM source_profiles ORDER BY source_id").fetchdf()
            df.to_csv(out_path, index=False)

    def export_source_profiles_parquet(self, out_path: Path) -> None:
        with self._lock:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            df = self.conn.execute("SELECT * FROM source_profiles ORDER BY source_id").fetchdf()
            df.to_parquet(out_path, index=False)

    def export_review_sources_csv(self, out_path: Path) -> None:
        with self._lock:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            sql = """
            SELECT * FROM source_profiles
            WHERE best_strategy IN ('manual_review','metadata_only')
               OR captcha_detected = TRUE
               OR login_detected = TRUE
               OR paywall_detected = TRUE
               OR html_status_code >= 400
               OR error_message IS NOT NULL
            ORDER BY source_id
            """
            df = self.conn.execute(sql).fetchdf()
            df.to_csv(out_path, index=False)


def new_id() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
