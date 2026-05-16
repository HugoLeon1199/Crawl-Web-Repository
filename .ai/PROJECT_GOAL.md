# Project Goal

## Project Name

Leon Global Web Intelligence Engine

## One-Line Goal

Build a global web intelligence system that can read many trusted web sources, automatically detect the best crawl strategy, collect structured data, and prepare it for AI summarization and analysis.

## Why This Project Matters

Leon wants a long-term data foundation for:

- global news monitoring
- science and technology tracking
- market intelligence
- trading research
- business research
- future AI automation products

The goal is not just scraping websites. The goal is to build a reliable information acquisition pipeline.

## Current Phase

Phase 1 — Universal Source Profiler + Smart Crawl Starter

## Current Technical Goal

Given a list of source links in:

```text
config/sources_raw.txt
```

The system should automatically detect the best strategy for each source:

- api_first
- rss_then_article_extract
- sitemap_then_article_extract
- html_then_trafilatura
- playwright_fallback
- metadata_only
- manual_review

## Expected Outputs

- data/db/web_intel.duckdb
- data/exports/source_profiles.csv
- data/exports/source_profiles.parquet
- data/exports/review_sources.csv
- data/exports/profile_summary.md
- logs/app.log

## Core Principles

1. API first.
2. RSS second.
3. Sitemap third.
4. Static HTML fourth.
5. Playwright only as fallback.
6. Never bypass CAPTCHA, login, paywall, or access control.
7. Store raw data separately from clean extracted data.
8. Always log failures per source.
9. The system should be resumable and safe.
10. The first version should be reliable, not overly complex.

## Tech Stack

- Python 3.11+
- httpx
- BeautifulSoup
- lxml
- feedparser
- trafilatura
- DuckDB
- pandas
- pydantic
- pyyaml
- loguru
- tenacity
- pyarrow
- Playwright as optional fallback

## Definition of Done

The current phase is done when:

1. The project can read 200 URLs from `config/sources_raw.txt`.
2. The profiler can assign a best strategy to each source.
3. Results are saved to DuckDB, CSV, and Parquet.
4. Difficult sources are exported to `review_sources.csv`.
5. The system can sample crawl a few articles per active source.
6. The code has clear modules, logging, error handling, and documentation.
7. Cursor writes implementation reports.
8. GPT and Gemini can review based on repository files.
