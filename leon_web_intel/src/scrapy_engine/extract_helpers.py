"""Shared HTML checks + trafilatura extraction for Scrapy spiders/pipelines."""

from __future__ import annotations

import trafilatura
from pydantic import BaseModel

from utils.hashing import sha256_text


class ExtractOutcome(BaseModel):
    title: str | None = None
    published_at: str | None = None
    content: str | None = None
    content_length: int = 0
    content_hash: str = ""
    language: str | None = None


def access_control_triplet(html: str, paywall_keywords: list[str], login_keywords: list[str], captcha_keywords: list[str]) -> tuple[bool, bool, bool]:
    lower = html.lower()
    paywall = any(k.lower() in lower for k in paywall_keywords)
    login = any(k.lower() in lower for k in login_keywords)
    captcha = any(k.lower() in lower for k in captcha_keywords)
    return paywall, login, captcha


def extract_with_trafilatura(html: str) -> ExtractOutcome:
    meta = trafilatura.extract_metadata(html)
    content = trafilatura.extract(html) or ""
    stripped = content.strip()
    title = meta.title if meta and meta.title else None
    pub = meta.date if meta and meta.date else None
    language = meta.language if meta and meta.language else None
    content_hash = sha256_text(stripped) if stripped else ""
    return ExtractOutcome(
        title=title,
        published_at=str(pub) if pub else None,
        content=stripped if stripped else None,
        content_length=len(stripped),
        content_hash=content_hash,
        language=language,
    )
