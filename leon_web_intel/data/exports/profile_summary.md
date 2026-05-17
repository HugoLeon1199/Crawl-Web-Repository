# Profile Summary

- total_sources: 10
- active_sources: 10
- active_candidate_sources: 0
- review_sources: 0
- error_sources: 0

## Strategy Breakdown

- api_first: 2
- rss_then_article_extract: 4
- sitemap_then_article_extract: 4
- html_then_trafilatura: 0
- playwright_fallback: 0
- metadata_only: 0
- manual_review: 0

## Readiness

Top 20 ready sources:

source_id | domain | best_strategy | rss | sitemap | html_ok
--- | --- | --- | --- | --- | ---
gdeltproject_org | gdeltproject.org | api_first | False | False | True
worldbank_org | worldbank.org | api_first | False | True | True
aljazeera_com | aljazeera.com | rss_then_article_extract | True | True | True
apnews_com | apnews.com | sitemap_then_article_extract | False | True | True
bbc_com | bbc.com | sitemap_then_article_extract | False | True | True
dw_com | dw.com | sitemap_then_article_extract | False | True | False
france24_com | france24.com | rss_then_article_extract | True | True | True
reutersagency_com | reutersagency.com | sitemap_then_article_extract | False | True | True
theguardian_com | theguardian.com | rss_then_article_extract | True | True | True
un_org | un.org | rss_then_article_extract | True | False | True

## Sources Needing Review

source_id | domain | reason | error_message
--- | --- | --- | ---

## Next Steps

- crawl sample active sources
- review metadata_only
- add API adapters for top official sources
- expand sources after v1 stable
