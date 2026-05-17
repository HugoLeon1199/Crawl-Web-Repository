# Final Crawl Report

## Run Summary
- Run ID: 72f7fe6c-1276-4203-b5a5-c73e97ac2de3
- Status: success
- Started at: 2026-05-17 12:49:41.798144
- Ended at: 2026-05-17 12:51:20.008703
- Input path: config\sources_raw.txt
- Strategy: rss
- Limit sources: 12
- Max articles per source: 100
- Force refresh: True

## Totals
- Sources: 16
- Discovered URLs: 0
- Frontier pending: 0
- Frontier crawling: 0
- Frontier crawled: 24
- Frontier failed: 7
- Frontier skipped: 43
- Articles: 24
- Errors: 122

## Articles By Strategy
- rss_then_article_extract: 22
- sitemap_then_article_extract: 2

## Errors By Type
- AccessControlDetected: 115
- ShortContent: 7

## Top Sources By Articles
- aljazeera_com: 15
- france24_com: 6
- bbc_com: 2
- un_org: 1

## Top Sources By Errors
- theguardian_com: 74
- france24_com: 22
- aljazeera_com: 18
- apnews_com: 2
- dw_com: 2
- reutersagency_com: 2
- un_org: 2

## Quality And Content
- Average quality_score: 9.6667
- Content length min: 306
- Content length avg: 2517.92
- Content length max: 10419

## Safety Notes
- robots obey enabled
- no captcha bypass
- no login automation
- no paywall bypass
- Playwright not part of Scrapy production path in this phase

## Limitations
- local DuckDB
- bounded Scrapy crawl
- no distributed scheduler yet
