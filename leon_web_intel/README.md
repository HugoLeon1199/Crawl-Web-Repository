# Leon Global Web Intelligence Engine (v1)

Local-first pipeline to **profile hundreds of web sources** without hand-labeling fetch strategies, then run **bounded production crawls** or a **timezone-aware “today” mode** that collects every publicly discoverable article for a calendar day (RSS / sitemap / bounded HTML). Outputs land in **DuckDB**, **CSV/Parquet**, and **Markdown** summaries.

## Installation

Requirements: **Python 3.11+**

```bash
cd leon_web_intel
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
python -m pip install -r requirements.txt
```

Optional Playwright browsers (only if you pass `--with-playwright`):

```bash
python -m playwright install chromium
```

## Prepare `config/sources_raw.txt`

- One URL per line  
- Lines starting with `#` are comments  
- Blank lines ignored  

The engine normalizes URLs, dedupes by registrable-style domain (drops `www.` for identity), and assigns a stable `source_id` (e.g. `bbc_com`).

## Dry run (no HTTP)

```bash
python run_profile.py --input config/sources_raw.txt --dry-run
```

## Profile all sources

```bash
python run_profile.py --input config/sources_raw.txt --profile-only
```

Options:

- `--limit 20` — profile only first N **unique domains** after dedupe  
- `--concurrency 5` — parallel workers (each worker shares a locked HTTP client + cache)  
- `--force-refresh` — ignore cached profiles newer than `--cache-days`  
- `--cache-days 7` — resume window  
- `--no-export-csv` / `--no-export-parquet` — disable exports  

## Scrapy production crawl layer (Phase 3 scaffold)

After profiles exist in DuckDB, the **Scrapy** layer performs a bounded production-style crawl. It does **not** replace SourceProfiler and is **not** a peer strategy to RSS/API/HTML detection—it only **executes** rows whose `best_strategy` is already `rss_then_article_extract`, `sitemap_then_article_extract`, or `html_then_trafilatura`.

**Standard flow**

1. Profile / refresh strategies (universal profiler + sample v1):

```bash
python run_profile.py --input config/sources_raw.txt --profile-only --limit 10 --force-refresh
```

2. Run Scrapy lanes (reads `data/db/web_intel.duckdb`, obeys robots.txt, same governance keywords as v1):

```bash
python run_scrapy.py --strategy all --limit 10 --max-articles-per-source 3
```

Lanes:

- `run_profile.py` — SourceProfiler + optional **sample** crawl (httpx/trafilatura).  
- `run_scrapy.py` — **Scrapy** crawl engine: RSS → article URLs, sitemap → article URLs, or shallow HTML link crawl from homepage.

Scrapy respects **`ROBOTSTXT_OBEY = True`**, uses **User-Agent / timeout / retries / delay** from `config/crawl_rules.yaml`, keeps **low per-domain concurrency**, and does **not** bypass paywall, login, or CAPTCHA (keyword gates match v1; blocked pages log `AccessControlDetected` without persisting full article content).

Skipped in this phase (sources are not loaded for Scrapy): `api_first`, `metadata_only`, `manual_review`, `playwright_fallback`. HTML lane skips sources with `robots_can_fetch_homepage = false`.

## TODAY FULL ARTICLE CRAWL

Collect **all publicly discoverable articles for one calendar day** per source (RSS entry dates, sitemap `lastmod`, and bounded homepage/link discovery with URL date heuristics). Governed the same way as v1: **no paywall/login/CAPTCHA bypass**, no proxy/stealth, no private content.

**Primary command**

```bash
python run_today.py --input config/sources_raw.txt --strategy all --date today --timezone Europe/Amsterdam --profile-limit 198 --max-urls-per-source 1000 --step-timeout-seconds 1800 --close-spider-timeout 1200
```

Direct Scrapy (after profiling), today-only:

```bash
python run_scrapy.py --strategy all --today-only --date today --timezone Europe/Amsterdam --max-urls-per-source 1000 --close-spider-timeout 900 --limit 198
```

Today-filtered exports + report:

```bash
python run_export.py --today-only --date today --timezone Europe/Amsterdam
```

**Main outputs**

| Artifact | Path |
|----------|------|
| Today articles CSV | `data/exports/today_articles.csv` |
| Today articles Parquet | `data/exports/today_articles.parquet` |
| Today crawl errors | `data/exports/today_crawl_errors.csv` |
| Today frontier snapshot | `data/exports/today_crawl_frontier.csv` |
| Today source health slice | `data/exports/today_source_health.csv` |
| Today Markdown report | `data/exports/today_final_report.md` |

Full-database exports (`articles.csv`, `final_crawl_report.md`, …) are still written whenever you run `run_export.py`.

## Production-ready E2E Crawl Foundation

This phase wires the durable crawl foundation end to end:

```bash
python run_pipeline.py --input config/sources_raw.txt --limit 20 --max-articles-per-source 3 --strategy all --force-refresh
```

Flow:

1. `sources_raw.txt` -> `run_profile.py --profile-only`
2. persisted source profiles -> Scrapy crawl lanes
3. article attempts -> `crawl_frontier`
4. successful extracts -> `articles`
5. failures/skips -> `crawl_errors` plus frontier state
6. current DB -> `source_health`
7. exports -> final Markdown report

`--limit` and `--max-articles-per-source` are for small, bounded test runs. The schema and pipeline are designed so a larger run later can increase limits/config without replacing the core architecture.

Outputs:

| Artifact | Path |
|----------|------|
| Articles CSV | `data/exports/articles.csv` |
| Articles Parquet | `data/exports/articles.parquet` |
| Crawl errors CSV | `data/exports/crawl_errors.csv` |
| Discovered URLs CSV | `data/exports/discovered_urls.csv` |
| Crawl frontier CSV | `data/exports/crawl_frontier.csv` |
| Source health CSV | `data/exports/source_health.csv` |
| Final crawl report | `data/exports/final_crawl_report.md` |

The foundation includes `crawl_runs`, `crawl_frontier`, and `source_health` tables for incremental crawl state, retry accounting, audit history, and source-level health. It intentionally does not add distributed crawling, Redis, Airflow, dashboards, AI summaries, proxy rotation, stealth browsing, login automation, CAPTCHA bypass, or paywall bypass.

You can regenerate exports without crawling:

```bash
python run_export.py
```

## Sample crawl (light touch)

Runs profiling first (respects resume), then fetches a **few URLs per source** according to `best_strategy`:

```bash
python run_profile.py --input config/sources_raw.txt --crawl-sample --max-articles-per-source 5
```

Playwright (optional):

```bash
python run_profile.py --input config/sources_raw.txt --crawl-sample --max-articles-per-source 5 --with-playwright
```

## Outputs

| Artifact | Path |
|----------|------|
| DuckDB | `data/db/web_intel.duckdb` |
| Profiles CSV | `data/exports/source_profiles.csv` |
| Profiles Parquet | `data/exports/source_profiles.parquet` |
| Review CSV | `data/exports/review_sources.csv` |
| Markdown summary | `data/exports/profile_summary.md` |
| HTTP cache | `data/cache/http/` |
| Raw HTML/RSS/sitemap/API | `data/raw/...` |
| Logs | `logs/app.log` |

See **`docs/data_contract.md`** for schemas and field meanings.

## Strategy decision tree

1. Known API adapter domain → `api_first`  
2. Else valid RSS/Atom → `rss_then_article_extract`  
3. Else valid sitemap → `sitemap_then_article_extract`  
4. Else trafilatura extract on homepage OK → `html_then_trafilatura`  
5. Else JS-heavy heuristic → `playwright_fallback`  
6. Else paywall/login/CAPTCHA **signals** → `metadata_only`  
7. Else → `manual_review`  

RSS beats sitemap; known API beats all. Domains listed under `prefer_metadata_only_domains` in `config/crawl_rules.yaml` downgrade heavy HTML/Playwright paths to `metadata_only` for governance.

## Safety / governance

- Polite **User-Agent**, **timeouts**, **retries**, **per-domain delay**, bounded concurrency  
- **No** CAPTCHA bypass, **no** login automation, **no** paywall bypass, **no** proxy rotation, **no** stealth drivers  
- Playwright is **opt-in** (`--with-playwright`) and still avoids logins/CAPTCHA cracking  

## Troubleshooting

- **`playwright_fallback` but no articles**: pass `--with-playwright` and ensure browsers installed.  
- **Empty RSS/sitemap**: site may need different paths; tune YAML lists in `crawl_rules.yaml`.  
- **Many `manual_review`**: origin may block bots (403), require cookies, or needs manual allowance.  

## Tests

```bash
python -m pytest
```

On GitHub Actions, each run uploads **Artifacts** named `leon-web-intel-ci-results`: open the workflow run → **Artifacts** at the bottom → download the zip. Inside you get `pytest-junit.xml` (machine-readable test report) and `dry_run.txt` (stdout from `run_profile.py --dry-run`).

## Next steps (beyond v1)

- Expand Scrapy integration (per-URL robots, richer scheduling, metrics) without coupling spiders to profiler internals  
- Real per-adapter API collectors (GDELT, OpenAlex, SEC EDGAR, …)  
- Stronger article URL ranking from sitemaps  
- robots.txt enforcement in collectors  
- Scheduling / incremental crawl state machines  
