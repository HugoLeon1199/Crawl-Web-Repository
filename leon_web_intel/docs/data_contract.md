# Data contract — Leon Web Intelligence v1

This document describes persisted artifacts produced by the profiler and sample crawler.

## `source_profiles` (DuckDB table)

One row per canonical `source_id` (domain-derived).

| Column | Type | Meaning |
|--------|------|---------|
| source_id | TEXT | Primary key; slug from domain (`bbc_com`) |
| input_url | TEXT | First URL seen for this domain |
| normalized_url | TEXT | Canonical normalized URL |
| domain | TEXT | Lowercase host without `www.` |
| scheme | TEXT | Usually `https` |
| homepage_url | TEXT | Normalized homepage used for probes |
| robots_url | TEXT | Fetched robots.txt URL |
| robots_ok | BOOLEAN | Parser/fetch succeeded enough to record signals |
| robots_sitemaps | TEXT | JSON list of sitemap URLs declared in robots.txt |
| robots_disallow_detected | BOOLEAN | Heuristic: non-empty `Disallow` paths seen |
| robots_can_fetch_homepage | BOOLEAN | `urllib.robotparser.can_fetch(User-Agent, homepage_url)` |
| has_known_api | BOOLEAN | Domain matched `known_api_adapters.yaml` |
| known_api_adapter | TEXT | Adapter name (placeholder in v1) |
| known_api_endpoint_hint | TEXT | Optional API doc/query endpoint |
| has_rss | BOOLEAN | At least one validated RSS/Atom URL |
| rss_urls | TEXT | JSON list of validated feed URLs |
| rss_valid_count | INTEGER | Count of validated feeds |
| has_sitemap | BOOLEAN | At least one validated sitemap URL |
| sitemap_urls | TEXT | JSON list of validated sitemap URLs |
| sitemap_url_count | INTEGER | Count validated |
| html_status_code | INTEGER | Homepage HTTP status |
| html_title | TEXT | `<title>` text |
| html_text_length | INTEGER | Rough visible text length |
| html_link_count | INTEGER | Number of `<a href>` |
| html_extract_ok | BOOLEAN | Trafilatura extract ≥ `min_extract_text_length` |
| sample_extracted_text_length | INTEGER | Length of extracted text on homepage |
| js_required | BOOLEAN | JS-heavy heuristic |
| paywall_detected | BOOLEAN | Keyword signals |
| captcha_detected | BOOLEAN | Keyword signals |
| login_detected | BOOLEAN | Keyword signals |
| best_strategy | TEXT | Selected crawl strategy |
| tos_risk | TEXT | `low` / `medium` / `high` / `unknown` |
| status | TEXT | `active` / `active_candidate` / `review` |
| error_message | TEXT | Profiler exception summary if any |
| profiled_at | TIMESTAMP | UTC profiling time |

## `discovered_urls`

Candidate URLs found during profiling-adjacent sampling steps.

| Column | Meaning |
|--------|---------|
| id | UUID primary key |
| source_id | Owning source |
| url | Discovered URL |
| discovery_method | e.g. `rss_feed`, `sitemap`, `api_placeholder_ready` |
| title | Optional title from feed |
| published_at | Optional publication string |
| raw_metadata | JSON blob |
| discovered_at | Timestamp |
| url_hash | SHA-256 of URL string |

## `articles`

Extracted documents from sample crawl.

| Column | Meaning |
|--------|---------|
| id | UUID |
| source_id | Owning source |
| url | Article URL |
| title | Extracted title |
| published_at | Optional date string |
| content | Plain text content |
| content_length | Character length |
| content_hash | SHA-256 of content |
| language | Optional language code |
| crawl_strategy_used | Strategy during crawl |
| raw_path | Filesystem path to raw HTML when saved |
| extracted_at | Timestamp |
| quality_score | Heuristic 0–10 |

## `crawl_errors`

Non-fatal failures per stage.

## `best_strategy` values

| Value | Meaning |
|-------|---------|
| api_first | Prefer official/API endpoints (adapters to be implemented per source) |
| rss_then_article_extract | Use feeds then per-article extraction |
| sitemap_then_article_extract | Discover URLs via sitemap indices/urlsets |
| html_then_trafilatura | Follow internal links + trafilatura |
| playwright_fallback | Likely needs rendered DOM |
| metadata_only | Store light metadata only (rights/paywall-sensitive) |
| manual_review | Insufficient automated signal |

## `status` values

| status | Meaning |
|--------|---------|
| active | Ready for RSS/sitemap/API-first automation |
| active_candidate | Likely OK but needs verification (HTML/Playwright path) |
| review | Needs human decision |

## `tos_risk`

- **low** — structured/open data style adapters  
- **medium** — conventional web crawling risk profile  
- **high** — publisher sensitivity or blocking signals  
- **unknown** — insufficient signal  

## `quality_score` (articles)

Heuristic score clamped to **[0, 10]** combining title presence, length, date presence, host validity, duplicate hash penalty, paywall/login/CAPTCHA signals, extraction success, and raw file existence. Intended for **relative ranking inside v1**, not legal/compliance proof.
