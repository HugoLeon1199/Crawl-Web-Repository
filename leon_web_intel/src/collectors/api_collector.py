"""Legacy placeholder markers for known API domains.

Production API ingestion runs through ``run_api_today.py`` (API Hub v1) and
``collectors/api_adapters/``. This module remains for lightweight discovery hints only.
"""

from __future__ import annotations

import json

from storage.db import WebIntelDB, new_id, utc_now
from utils.hashing import sha256_text


def record_api_placeholder(
    *,
    source_id: str,
    endpoint_hint: str | None,
    adapter: str | None,
    db: WebIntelDB,
) -> None:
    hint = endpoint_hint or ""
    row = {
        "id": new_id(),
        "source_id": source_id,
        "url": hint,
        "discovery_method": "api_placeholder_ready",
        "title": None,
        "published_at": None,
        "raw_metadata": json.dumps({"adapter": adapter, "endpoint_hint": endpoint_hint}),
        "discovered_at": utc_now(),
        "url_hash": sha256_text(hint or source_id),
    }
    db.insert_discovered_url(row)
