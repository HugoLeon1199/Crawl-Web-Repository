"""DuckDB persistence."""

from __future__ import annotations

import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb


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
"""


class WebIntelDB:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self.conn = duckdb.connect(str(db_path))
        self.conn.execute(DDL)
        self._migrate_source_profiles_robots_fetch()

    def _migrate_source_profiles_robots_fetch(self) -> None:
        """Add robots_can_fetch_homepage for DBs created before this column existed."""
        try:
            self.conn.execute(
                "ALTER TABLE source_profiles ADD COLUMN robots_can_fetch_homepage BOOLEAN DEFAULT TRUE"
            )
        except Exception:
            # DuckDB leaves the transaction aborted if ALTER fails (e.g. column already in DDL).
            try:
                self.conn.execute("ROLLBACK")
            except Exception:
                pass

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
