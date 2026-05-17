"""Offline tests for API Hub v1 (no live HTTP)."""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

import httpx
import pytest

from collectors.api_adapters.arxiv import parse_arxiv_atom
from collectors.api_adapters.crossref import parse_crossref_message_items
from collectors.api_adapters.gdelt import parse_gdelt_article_dict
from collectors.api_adapters.github_api import parse_github_search_repositories
from collectors.api_adapters.openalex import parse_openalex_works_response
from collectors.api_adapters.pubmed import parse_pubmed_esummary
from collectors.api_adapters.registry import resolve_adapter_names
from collectors.api_adapters.sec_edgar import parse_sec_submissions_json
from collectors.api_adapters.semantic_scholar import parse_semantic_scholar_search
from collectors.api_adapters.world_bank import parse_world_bank_indicator_response
from collectors.api_adapters.base import ApiAdapter, ApiRecord
from run_api_today import run_api_hub
from settings import load_crawl_rules
from storage.db import WebIntelDB
from storage.raw_store import RawStore
from utils.today_filter import target_date_range


ROOT = Path(__file__).resolve().parents[1]


def test_gdelt_parse_response() -> None:
    rec = parse_gdelt_article_dict(
        {"url": "https://example.org/news/1", "title": " Hello ", "domain": "example.org", "language": "en"}
    )
    assert rec is not None
    assert rec.url.startswith("http")
    assert rec.record_type == "news_article"


def test_openalex_parse_response() -> None:
    data = {
        "results": [
            {
                "id": "https://openalex.org/W123",
                "display_name": "Paper",
                "publication_date": "2024-01-01",
                "language": "en",
                "primary_location": {"landing_page_url": "https://journal.example/p/1"},
                "authorships": [{"author": {"display_name": "A. Author"}}],
            }
        ]
    }
    rows = parse_openalex_works_response(data)
    assert len(rows) == 1
    assert rows[0].title == "Paper"


def test_arxiv_parse_response() -> None:
    xml = b"""<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2401.00001</id>
    <title>Sample Title</title>
    <published>2024-01-02T00:00:00Z</published>
    <summary>Abstract text here.</summary>
  </entry>
</feed>"""
    rows = parse_arxiv_atom(xml)
    assert len(rows) == 1
    assert "arxiv.org" in rows[0].url


def test_sec_parse_response() -> None:
    data = {
        "cik": "1234567",
        "name": "Demo Co",
        "filings": {
            "recent": {
                "form": ["10-K"],
                "filingDate": ["2024-06-01"],
                "accessionNumber": ["0001-22-000001"],
                "primaryDocument": ["primary.htm"],
            }
        },
    }
    rows = parse_sec_submissions_json(data, target_filing_date="2024-06-01")
    assert len(rows) == 1
    assert rows[0].record_type == "sec_filing"


def test_world_bank_parse_response() -> None:
    payload = [
        {"page": 1},
        [
            {
                "countryiso3code": "USA",
                "date": "2023",
                "value": 123,
                "indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP"},
            }
        ],
    ]
    rows = parse_world_bank_indicator_response(payload)
    assert len(rows) == 1
    assert rows[0].record_type == "macro_data"


def test_pubmed_parse_response() -> None:
    result = {
        "result": {
            "uids": ["12345"],
            "12345": {
                "title": "Gene discovery",
                "fulljournalname": "Journal",
                "pubdate": "2024 Jan 1",
                "authors": [{"name": "Smith J"}],
            },
        }
    }
    rows = parse_pubmed_esummary(result)
    assert len(rows) == 1
    assert "pubmed.ncbi.nlm.nih.gov" in rows[0].url


def test_github_parse_response() -> None:
    data = {
        "items": [
            {
                "html_url": "https://github.com/o/r",
                "full_name": "o/r",
                "description": "desc",
                "stargazers_count": 3,
                "language": "Rust",
                "updated_at": "2024-01-02T00:00:00Z",
                "pushed_at": "2024-01-03T00:00:00Z",
                "owner": {"login": "o"},
            }
        ]
    }
    rows = parse_github_search_repositories(data)
    assert len(rows) == 1
    assert rows[0].api_name == "github"


def test_crossref_parse_response() -> None:
    msg = {
        "items": [
            {
                "DOI": "10.1234/example",
                "title": ["Crossref work"],
                "issued": {"date-parts": [[2024, 2, 1]]},
                "URL": "https://doi.org/10.1234/example",
                "author": [{"given": "Ann", "family": "Bee"}],
                "publisher": "PubCo",
            }
        ]
    }
    rows = parse_crossref_message_items(msg)
    assert len(rows) == 1
    assert rows[0].record_type == "scholarly_work"


def test_semantic_scholar_parse_response() -> None:
    data = {
        "data": [
            {
                "paperId": "abc",
                "title": "SS paper",
                "year": 2024,
                "publicationDate": "2024-03-01",
                "abstract": "Abstract.",
                "authors": [{"name": "Someone"}],
                "url": "https://www.semanticscholar.org/paper/abc",
                "citationCount": 9,
            }
        ]
    }
    rows = parse_semantic_scholar_search(data)
    assert len(rows) == 1
    assert rows[0].title == "SS paper"


def test_resolve_adapter_names_all_count() -> None:
    adapters = resolve_adapter_names("all")
    assert len(adapters) == 9


def test_api_runner_continue_on_error(tmp_path: Path) -> None:
    class Boom(ApiAdapter):
        name = "boom"

        def collect_today(self, **kwargs):  # noqa: ANN003
            raise RuntimeError("boom")

    class Ok(ApiAdapter):
        name = "ok"

        def collect_today(self, **kwargs):  # noqa: ANN003
            return [
                ApiRecord(
                    source_id="src_ok",
                    api_name="ok",
                    record_type="test",
                    title="Hi",
                    url="https://example.com/api-hub-test",
                )
            ]

    db_path = tmp_path / "t.duckdb"
    db = WebIntelDB(db_path)
    raw_store = RawStore(tmp_path / "raw")
    rules = load_crawl_rules(ROOT / "config" / "crawl_rules.yaml")
    transport = httpx.MockTransport(lambda req: httpx.Response(200, json={}))
    client = httpx.Client(transport=transport)
    try:
        run_api_hub(
            db=db,
            rules=rules,
            adapters=[Boom(), Ok()],
            target_date_str="today",
            timezone_name="UTC",
            query="*",
            max_records=10,
            extract_content=False,
            continue_on_error=True,
            clear_calendar_day=False,
            raw_store=raw_store,
            client=client,
        )
        rows = db.fetch_today_api_records(target_date_str="today", timezone_name="UTC")
        assert len(rows) == 1
        assert rows[0]["api_name"] == "ok"
    finally:
        client.close()
        db.close()


def test_api_runner_fail_fast(tmp_path: Path) -> None:
    class Boom(ApiAdapter):
        name = "boom"

        def collect_today(self, **kwargs):  # noqa: ANN003
            raise RuntimeError("boom")

    db_path = tmp_path / "t.duckdb"
    db = WebIntelDB(db_path)
    raw_store = RawStore(tmp_path / "raw")
    rules = load_crawl_rules(ROOT / "config" / "crawl_rules.yaml")
    client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json={})))
    try:
        with pytest.raises(RuntimeError, match="boom"):
            run_api_hub(
                db=db,
                rules=rules,
                adapters=[Boom()],
                target_date_str="2020-01-15",
                timezone_name="UTC",
                query="*",
                max_records=10,
                extract_content=False,
                continue_on_error=False,
                clear_calendar_day=False,
                raw_store=raw_store,
                client=client,
            )
    finally:
        client.close()
        db.close()


def test_api_metadata_export_no_crash(tmp_path: Path) -> None:
    db_path = tmp_path / "t.duckdb"
    db = WebIntelDB(db_path)
    start, _ = target_date_range("2020-01-15", "UTC")
    mid = start + timedelta(hours=2)
    try:
        db.insert_api_record(
            {
                "id": "rid1",
                "api_name": "unit",
                "source_id": "unit",
                "record_type": "test",
                "title": "T",
                "url": "https://example.com/u1",
                "published_at": None,
                "updated_at": None,
                "summary": None,
                "content": None,
                "language": None,
                "domain": None,
                "country": None,
                "authors_json": None,
                "raw_metadata": "{}",
                "discovery_method": "test",
                "content_hash": "x",
                "collected_at": mid,
                "target_calendar_date": "2020-01-15",
                "timezone_name": "UTC",
            }
        )
        out_csv = tmp_path / "meta.csv"
        db.export_today_api_metadata_csv(out_csv, target_date_str="2020-01-15", timezone_name="UTC")
        assert out_csv.is_file()
        assert "unit" in out_csv.read_text(encoding="utf-8")
    finally:
        db.close()


def test_today_ai_input_jsonl_export(tmp_path: Path) -> None:
    db_path = tmp_path / "t.duckdb"
    db = WebIntelDB(db_path)
    start, _ = target_date_range("2020-01-15", "UTC")
    mid = start + timedelta(hours=2)
    try:
        db.insert_article(
            {
                "id": "art1",
                "source_id": "s1",
                "url": "https://example.com/a",
                "title": "Article",
                "published_at": None,
                "content": "body text " * 40,
                "content_length": 400,
                "content_hash": "h",
                "language": "en",
                "crawl_strategy_used": "rss_then_article_extract",
                "raw_path": "",
                "extracted_at": mid,
                "quality_score": 5.0,
            }
        )
        db.insert_api_record(
            {
                "id": "rid2",
                "api_name": "unit",
                "source_id": "unit",
                "record_type": "test",
                "title": "API row",
                "url": "https://example.com/u2",
                "published_at": None,
                "updated_at": None,
                "summary": "short summary",
                "content": None,
                "language": None,
                "domain": None,
                "country": None,
                "authors_json": None,
                "raw_metadata": "{}",
                "discovery_method": "test",
                "content_hash": "y",
                "collected_at": mid,
                "target_calendar_date": "2020-01-15",
                "timezone_name": "UTC",
            }
        )
        out_path = tmp_path / "ai.jsonl"
        db.export_today_ai_input_jsonl(out_path, target_date_str="2020-01-15", timezone_name="UTC")
        lines = out_path.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 2
        o0 = json.loads(lines[0])
        o1 = json.loads(lines[1])
        assert o0["source_type"] == "scrapy"
        assert o1["source_type"] == "api"
        assert "content_length" in o0
    finally:
        db.close()
