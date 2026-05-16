# Leon Global Web Intelligence Engine (v1)

Local-first pipeline to **profile hundreds of web sources** without hand-labeling fetch strategies, then run a **small sample crawl** per detected strategy. Outputs land in **DuckDB**, **CSV/Parquet**, and **Markdown** summaries.

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

## Next steps (beyond v1)

- Real per-adapter API collectors (GDELT, OpenAlex, SEC EDGAR, …)  
- Stronger article URL ranking from sitemaps  
- robots.txt enforcement in collectors  
- Scheduling / incremental crawl state machines  
