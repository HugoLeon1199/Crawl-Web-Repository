# CURSOR_WORKLOG — shared worklog

**Repo:** https://github.com/HugoLeon1199/Crawl-Web-Repository  
**Project:** Leon Global Web Intelligence Engine  

## Current session (2026-05-16) — Full TODAY crawl (`strategy all`): agent environment + safe metadata

### Mục tiêu kiểm tra

- Crawl toàn bộ bài public **hôm nay** mà hệ thống phát hiện được từ **tất cả** source trong `config/sources_raw.txt`, qua **RSS / sitemap / HTML**, không bypass paywall/login/captcha.
- **Không** commit nội dung full article lên GitHub; chỉ commit **`today_final_report.md`** + **`today_articles_metadata.csv`** (không cột `content`).

### Pytest (bước 1)

| Command | Result |
|---------|--------|
| `cd leon_web_intel` → `python -m pytest -v --tb=short` | **Không chạy được trên agent Cursor:** Windows `py -0p` trỏ `D:\python.exe` nhưng **`Test-Path D:\python.exe` → False** (interpreter hỏng/thiếu). Cần máy local có `python` hoặc sửa Python Install Manager / cài Python rồi chạy lại bước 1. |

### Full today crawl (bước 2)

| Command | Result |
|---------|--------|
| `python run_today.py --input config/sources_raw.txt --strategy all --date today --timezone Europe/Amsterdam --profile-limit 198 --max-urls-per-source 1000 --step-timeout-seconds 7200 --close-spider-timeout 3600 --force-refresh` | **Không chạy được trên agent** (thiếu `python`). |

**Lệnh copy-paste sau khi có Python (cwd `leon_web_intel`):**

```bash
python -m pytest -v --tb=short
python run_today.py --input config/sources_raw.txt --strategy all --date today --timezone Europe/Amsterdam --profile-limit 198 --max-urls-per-source 1000 --step-timeout-seconds 7200 --close-spider-timeout 3600 --force-refresh
```

### Run ID / status

- **Full `strategy all` run:** **chưa thực hiện** trên agent → **run_id:** *n/a* · **status:** *pending local execution*

### Target date / timezone (theo pipeline hiện tại)

- **`date today`** + **`Europe/Amsterdam`** → báo cáo đã có trong repo gần nhất (RSS smoke trước đó) khớp **2026-05-17** và cửa sổ UTC `2026-05-16 22:00` → `2026-05-17 22:00` (xem `today_final_report.md`).

### Baseline trong repo (RSS smoke — **không** phải full `strategy all`)

These numbers come from the latest checked-in **`today_final_report.md`** (profile-limit nhỏ / RSS path), **not** from a completed `--strategy all --profile-limit 198` run:

- **Today articles (exported filter):** **19**
- **Articles by strategy:** `rss_then_article_extract`: **19**
- **Top sources by article count:** `aljazeera_com`: **13**, `france24_com`: **6**
- **Total errors (UTC window):** **122**
- **AccessControlDetected:** **115**
- **ShortContent:** **7**
- **NotToday** (`crawl_errors` window): **0** · Frontier skipped **NotToday**: **0**

### Top 20 titles / URLs (19 rows — toàn bộ today slice baseline)

1. World Cup 2026: FIFA holds ‘positive’ talks with Iranian football officials — https://www.aljazeera.com/sports/2026/5/17/fifa-holds-positive-talks-with-iranian-football-officials-on-world-cup?traffic_source=rss  
2. WHO declares global health emergency over Ebola outbreak in Congo and Uganda — https://www.france24.com/en/health/20260517-who-declares-global-health-emergency-over-ebola-outbreak-in-congo-and-uganda  
3. WHO declares Ebola outbreak in DR Congo, Uganda a global health emergency — https://www.aljazeera.com/news/2026/5/17/who-declares-ebola-outbreak-in-dr-congo-uganda-a-global-health-emergency?traffic_source=rss  
4. Ukraine launches more than 500 drones at Russia in deadly overnight attack, authorities say — https://www.france24.com/en/europe/20260517-ukraine-launches-more-than-500-drones-at-russia-in-deadly-overnight-attack-authorities-say  
5. Sports - Manchester City see off Chelsea in FA Cup final and keep treble dream alive — https://www.france24.com/en/tv-shows/sports/20260517-manchester-city-see-off-chelsea-in-fa-cup-final-and-keep-treble-dream-alive  
6. Ronda Rousey retires again after 17-second submission defeat of Gina Carano — https://www.aljazeera.com/sports/2026/5/17/ronda-rousey-vs-gina-carano-fight-rousey-wins-with-a-17-second-submission?traffic_source=rss  
7. Modest fashion’s global turn — https://www.aljazeera.com/features/2026/5/17/modest-fashions-global?traffic_source=rss  
8. Middle East live: USS Ford returns from Iran war after longest deployment since Vietnam — https://www.france24.com/en/middle-east/20260517-middle-east-live-uss-ford-returns-from-iran-war-after-longest-deployment-since-vietnam  
9. Iran war day 79: Israel’s relentless bombardment of Lebanon continues — https://www.aljazeera.com/news/2026/5/17/iran-war-day-79-tehran-to-unveil-hormuz-toll-plan-israel-bombs-lebanon?traffic_source=rss  
10. Iran plans Hormuz tolls; Trump warns of ‘very bad time’ over stalled talks — https://www.aljazeera.com/news/liveblog/2026/5/17/iran-war-live-tehran-eyes-tolls-in-hormuz-trump-warns-of-very-bad-time?traffic_source=rss  
11. Bulgaria wins 2026 Eurovision, Israel lands a nail-biting second — https://www.france24.com/en/culture/20260517-bulgaria-s-bangaranga-wins-eurovision-with-israel-second  
12. Iraq’s new PM Ali al-Zaidi formally takes over — https://www.aljazeera.com/video/newsfeed/2026/5/17/aje-onl-nf_clip-iraqs-new-pm-al-zaidi-formally-takes-over-160526?traffic_source=rss  
13. Tunisians rally amid economic crisis and political arrests — https://www.aljazeera.com/video/newsfeed/2026/5/17/tunisians-rally-amid-economic-crisis-and-political-arrests?traffic_source=rss  
14. Activists troll far-right UK rally with giant pro-immigration clip — https://www.aljazeera.com/video/newsfeed/2026/5/17/aje-onl-nf_clip-led-by-donkeys-hijack-far-right-rally-160526?traffic_source=rss  
15. Algeria’s USM Alger beat Egypt’s Zamalek to win CAF Cup — https://www.aljazeera.com/video/newsfeed/2026/5/17/algerias-usm-alger-beat-egypts-zamalek-to-win-caf-cup?traffic_source=rss  
16. The week in pictures: Trump in China, Cannes festival and Philippines Senate shooting — https://www.france24.com/en/asia-pacific/20260517-the-week-in-pictures-trump-in-china-cannes-festival-philippine-senate-shooting  
17. ‘Timmy’ the rescued humpback whale confirmed dead — https://www.aljazeera.com/video/newsfeed/2026/5/17/timmy-the-rescued-humpback-whale-confirmed-dead?traffic_source=rss  
18. Could a leadership change undo Israel’s international isolation? — https://www.aljazeera.com/news/2026/5/17/could-a-leadership-change-undo-israels-international-isolation?traffic_source=rss  
19. India’s Tata and Dutch giant ASML sign semiconductor deal during Modi visit — https://www.aljazeera.com/news/2026/5/17/indias-tata-and-dutch-giant-asml-sign-semiconductor-deal-during-modi-visit?traffic_source=rss  

### Timeout / hang

- **Agent:** không vào được pipeline → không có timeout step.
- **Sau khi local chạy:** nếu `--strategy all` hết **7200s/step**, ghi rõ step (`run_profile` / `run_scrapy` / `run_export`) và chạy lần lượt `--strategy rss`, rồi `sitemap`, rồi `html` (cùng `--date`, `--timezone`, `--profile-limit 198`).

### Output files (bước 3–4)

| File | Ghi chú |
|------|---------|
| `data/exports/today_final_report.md` | Có trong repo (baseline smoke); **chưa** ghi đè bởi full crawl trên agent |
| `data/exports/today_articles.csv` / `.parquet` | **Không commit** (có full content) |
| `data/exports/today_crawl_errors.csv` | Local sau crawl; **không** commit trong scope “chỉ report + metadata” |
| `data/exports/today_crawl_frontier.csv` | Giống trên |
| `data/exports/today_source_health.csv` | Giống trên |
| `data/exports/today_articles_metadata.csv` | Chỉ các cột: `source_id`, `title`, `published_at`, `url`, `content_length`, `quality_score`, `crawl_strategy_used` — **đồng bộ code** trong `WebIntelDB.export_today_articles_metadata_csv`; slice trong repo regenerate từ DB crawl hiện có để khớp schema commit |

### Commit / push (bước 5 — agent)

- **Định commit:** `.ai/CURSOR_WORKLOG.md`, `leon_web_intel/data/exports/today_articles_metadata.csv`, và **fix code** `leon_web_intel/src/storage/db.py` + `leon_web_intel/tests/test_today_mode.py` (seven-column metadata).
- **Không** `git add`: `today_articles.csv`, `today_articles.parquet`.

### Code đổi trong phiên

- `export_today_articles_metadata_csv` chỉ ghi **7 cột** an toàn (thứ tự như trên).

---

## Current session (2026-05-17) — Giảm false positive AccessControlDetected (governance)

### Mục tiêu

Giữ **không bypass** paywall/login/CAPTCHA/proxy/stealth; làm governance **ít nhạy** với chữ *Subscribe / Sign in* ở chrome trang khi **main text trafilatura đã đủ dài**.

### Files modified / created

- `leon_web_intel/src/scrapy_engine/extract_helpers.py` — **extract-first semantics**: hard wall (captcha/bot marker, access denied), strong phrases (`login to continue`, `subscribe to continue`, …), rồi nếu `content_length >= min_article_content_length` thì **không** block soft keyword; nếu ngắn thì block khi soft keyword trong **body extract** hoặc **≥5** hit trên visible text (script/style stripped).
- `leon_web_intel/src/scrapy_engine/pipelines.py` — gọi `extract_with_trafilatura` **trước** `access_control_triplet(...)` (truyền `extracted_plain` + lengths).
- `leon_web_intel/tests/test_access_control_refined.py` — 4 test offline (public long + Subscribe nav; paywall phrase; captcha; login continue).

### Commands run

Interpreter: `D:\cursor\LEONCODE\CRAWL WEB\.tools\nuget_packages\python.3.11.9\tools\python.exe` (cwd `leon_web_intel`).

| Command | Result |
|---------|--------|
| `python -m pytest -v --tb=short` | **40 passed** (~3.4s) |
| `python run_today.py --input config/sources_raw.txt --strategy rss --date 2026-05-17 --timezone Europe/Amsterdam --profile-limit 12 --max-urls-per-source 100 --step-timeout-seconds 900 --close-spider-timeout 600 --force-refresh` | **Exit 0** |

### Smoke (`today_final_report.md`)

- **Run ID:** `72f7fe6c-1276-4203-b5a5-c73e97ac2de3` — **success**  
- **Today articles (export filter):** **19**  
- **Errors (UTC window):** **122** — **AccessControlDetected: 115**, **ShortContent: 7**  
- **NotToday** (`crawl_errors` trong cửa sổ): **0** · Frontier NotToday trong cửa sổ: **0**  

### Top articles (mẫu từ báo cáo)

1. Al Jazeera — World Cup 2026 / FIFA talks — `https://www.aljazeera.com/sports/2026/5/17/fifa-holds-positive-talks-with-iranian-football-officials-on-world-cup?traffic_source=rss`  
2. France24 — WHO Ebola emergency — `https://www.france24.com/en/health/20260517-who-declares-global-health-emergency-over-ebola-outbreak-in-congo-and-uganda`  
3. Al Jazeera — WHO Ebola DR Congo/Uganda — `https://www.aljazeera.com/news/2026/5/17/who-declares-ebola-outbreak-in-dr-congo-uganda-a-global-health-emergency?traffic_source=rss`  
*(đủ 10 dòng trong `today_final_report.md`)*  

### Outputs

- `leon_web_intel/data/exports/today_articles.csv` / `.parquet`  
- `leon_web_intel/data/exports/today_final_report.md`  
- `leon_web_intel/data/exports/today_crawl_errors.csv` (và các `today_*` khác sau `run_export --today-only`)

### So sánh nhanh

- Smoke RSS today **trước** chỉnh governance: **0** today articles, ~79 AccessControl trên batch nhỏ.  
- **Sau** chỉnh: **19** today articles cùng profile-limit 12 / RSS; vẫn còn AccessControl trên nhiều domain khác (đúng chỗ có gate thật hoặc HTML không đủ text).

---

## Current session (2026-05-17) — TODAY FULL ARTICLE CRAWL MODE (public discovery)

### Goal

Chuyển từ sample crawl sang **lấy toàn bộ bài có thể phát hiện công khai trong một ngày** (RSS dates / sitemap `lastmod` / HTML có giới hạn), có **`--timezone`** và **`--date`**, không bypass governance.

### Files created

- `leon_web_intel/src/utils/today_filter.py` — parse dates (RSS/ISO/RFC822/W3CDTF/YYYY-MM-DD), `target_date_range`, URL ngày trong path.  
- `leon_web_intel/run_today.py` — orchestrator profile → `run_scrapy.py --today-only` → `run_export.py --today-only`.  
- `leon_web_intel/tests/test_today_mode.py` — offline tests (RSS/sitemap/URL/export/report/command building).

### Files modified

- `leon_web_intel/src/scrapy_engine/items.py` — `discovered_at`, `candidate_published_at`, `discovery_source`, `target_date`, `is_today_candidate`.  
- `leon_web_intel/src/scrapy_engine/spiders/rss_article_spider.py` — today filter + `max_urls_per_source`.  
- `leon_web_intel/src/scrapy_engine/spiders/sitemap_article_spider.py` — `loc`+`lastmod` parsing, today filter.  
- `leon_web_intel/src/scrapy_engine/spiders/html_article_spider.py` — today discovery + caps (`max_urls_per_source`, depth 2).  
- `leon_web_intel/src/scrapy_engine/pipelines.py` — after extract: gate inserts with **NotToday** / **PublishedDateMissingLikelyToday**; đọc `WEB_INTEL_*` settings.  
- `leon_web_intel/src/scrapy_engine/settings.py`, `runner.py`, `run_scrapy.py` — `--today-only`, `--date`, `--timezone`, `--max-urls-per-source`.  
- `leon_web_intel/run_export.py` — `--today-only` → `today_*.csv|parquet|md`.  
- `leon_web_intel/src/reporting/crawl_report.py` — `write_today_crawl_report`.  
- `leon_web_intel/src/storage/db.py` — `fetch_today_articles`, `get_today_summary_stats`, `export_today_*`.  
- `leon_web_intel/tests/test_scrapy_layer.py` — assert default `WEB_INTEL_*` keys.  
- `leon_web_intel/README.md` — mục **TODAY FULL ARTICLE CRAWL**.  
- `.ai/CURSOR_WORKLOG.md` — mục này.

### Commands run

Interpreter: `D:\cursor\LEONCODE\CRAWL WEB\.tools\nuget_packages\python.3.11.9\tools\python.exe` (cwd `leon_web_intel`).

| Command | Result |
|---------|--------|
| `python -m pytest -v --tb=short` | **36 passed** (~4s) |
| `python run_today.py --input config/sources_raw.txt --strategy rss --date 2026-05-17 --timezone Europe/Amsterdam --profile-limit 12 --max-urls-per-source 100 --step-timeout-seconds 900 --close-spider-timeout 600 --force-refresh` | **Exit 0** — smoke (nhỏ hơn `--profile-limit 198` đầy đủ để agent kịp trong phiên) |

### Target ngày / timezone

- **`2026-05-17`** · **`Europe/Amsterdam`** (UTC window báo cáo: `2026-05-16 22:00 UTC` → `2026-05-17 22:00 UTC`)

### Run audit (smoke)

- **Run ID:** `5499a61b-9624-4884-9a9a-cf3f1930dc1c` — status **success**  
- **Today articles** (filter export): **0** — các URL RSS trong ngày vẫn bị **keyword governance** (`AccessControlDetected`) trên phần lớn domain tin lớn trong DB hiện tại.  
- **Errors (UTC window trong `today_final_report`):** **79** — toàn **AccessControlDetected**  
- **NotToday** (`crawl_errors` trong cửa sổ): **0**  
- **Frontier skipped NotToday** (trong cửa sổ): **0**  
- **AccessControlDetected:** **79**  

### Outputs

- `leon_web_intel/data/exports/today_articles.csv`  
- `leon_web_intel/data/exports/today_articles.parquet`  
- `leon_web_intel/data/exports/today_crawl_errors.csv`  
- `leon_web_intel/data/exports/today_crawl_frontier.csv`  
- `leon_web_intel/data/exports/today_source_health.csv`  
- `leon_web_intel/data/exports/today_final_report.md`  

### Top articles / URLs

- Không có hàng nào trong bảng Top Articles của `today_final_report.md` (**0** today rows sau filter).

### Timeout / hang

- **Không hang:** Scrapy ~**78s**, pipeline smoke ~**97s** tổng.  
- Để chạy đúng như spec đầy đủ:  
  `python run_today.py --input config/sources_raw.txt --strategy rss --date today --timezone Europe/Amsterdam --profile-limit 198 --max-urls-per-source 1000 --step-timeout-seconds 1800 --close-spider-timeout 1200`  
  rồi (nếu RSS ổn) `--strategy all` với timeout cao hơn như README.

---

## Current session (2026-05-17) — RSS scale batch limit 30 (pytest + pipeline)

Chỉ kiểm tra scale nhỏ–vừa: **RSS**, `--limit 30`, không đổi code (không có lỗi implementation).

### Commands run

Interpreter: `D:\cursor\LEONCODE\CRAWL WEB\.tools\nuget_packages\python.3.11.9\tools\python.exe` (cwd `leon_web_intel`).

| Command | Result |
|---------|--------|
| `python -m pytest -v --tb=short` | **29 passed** (~3.6s) |
| `python run_pipeline.py --input config/sources_raw.txt --limit 30 --max-articles-per-source 1 --strategy rss --force-refresh --step-timeout-seconds 300 --close-spider-timeout 240` | **Exit 124** — bước **`run_profile.py --profile-only --limit 30`** bị **`step-timeout-seconds 300`** khi profiler ~**16/30** nguồn; **`run_scrapy.py` không được chạy**; pipeline gọi **`run_export.py`** recovery (partial export) |

### Run audit (`final_crawl_report.md`)

- **Run ID:** `abf1e8ea-5713-4435-a774-a069f6294024`
- **Status:** **failed** (ghi nhận timeout profile subprocess)
- **Totals (DB sau export):** **Articles:** 3 · **Errors:** 17  
- **Frontier:** crawled **3** · skipped **14** · failed **0** (pending/crawling **0**)  
- **Top error types:** chỉ **AccessControlDetected** (17 trong báo cáo tổng hợp)

### Export files checked

- `leon_web_intel/data/exports/final_crawl_report.md` — đã đọc; run failed + số liệu trên khớp  
- `leon_web_intel/data/exports/articles.csv` — **3** bản ghi article (CSV nhiều dòng do field có newline)  
- `leon_web_intel/data/exports/crawl_errors.csv` — **17** dòng lỗi + header  
- `leon_web_intel/data/exports/crawl_frontier.csv` — **17** hàng dữ liệu + header (3 crawled, còn lại skipped/…)  
- `leon_web_intel/data/exports/source_health.csv` — **16** source_id (khớp profiler đã ghi **16** profile trước khi bị cắt)

### Timeout / hang

- **Không hang vô hạn:** subprocess profile bị **SIGTERM/kill theo `subprocess.run` timeout** sau ~**300s** wall-clock; **`run_export`** recovery chạy xong.  
- **Rút kinh nghiệm scale:** với **`--force-refresh --limit 30`**, **300s** có thể **không đủ** cho xong `profile-only` (vài domain chậm/HTML probe dài); muốn full 30 profile + RSS crawl trong một lần chạy thì cần **`--step-timeout-seconds`** cao hơn hoặc tách profile/crawl — **không đổi code trong phiên này.**

---

## Current session (2026-05-17) — `run_pipeline` step timeout + Scrapy `CLOSESPIDER_TIMEOUT` CLI

### Goal

Giữ pipeline **kết thúc sạch** trước full crawl: giới hạn thời gian từng bước subprocess, khi timeout vẫn **xuất partial** qua `run_export.py`; cho phép chỉnh **CLOSESPIDER_TIMEOUT** từ CLI.

### Files modified

- `leon_web_intel/run_pipeline.py` — `--step-timeout-seconds` (optional); `_run_step(..., timeout_seconds)`; on **TimeoutExpired**: `finish_crawl_run(..., failed)`, sau đó chạy **`run_export.py`** không áp timeout; `--close-spider-timeout` forward vào `run_scrapy.py`; `config_json` ghi thêm `step_timeout_seconds`, `close_spider_timeout`.
- `leon_web_intel/run_scrapy.py` — `--close-spider-timeout` (default 600).
- `leon_web_intel/src/scrapy_engine/runner.py` — `run_scrapy_engine(..., close_spider_timeout=600)`.
- `leon_web_intel/src/scrapy_engine/settings.py` — `build_scrapy_settings_dict` / `build_scrapy_settings` nhận `closespider_timeout`.
- `leon_web_intel/tests/test_crawl_foundation.py` — `build_pipeline_commands(..., close_spider_timeout=600)` + assert flag.
- `leon_web_intel/tests/test_scrapy_layer.py` — `test_scrapy_settings_closespider_timeout_override`.
- `.ai/CURSOR_WORKLOG.md` — mục này.

### Commands run

Interpreter: `D:\cursor\LEONCODE\CRAWL WEB\.tools\nuget_packages\python.3.11.9\tools\python.exe` (cwd `leon_web_intel`).

| Command | Result |
|---------|--------|
| `python -m pytest -v --tb=short` | **29 passed** (~4s) |
| `python run_pipeline.py --input config/sources_raw.txt --limit 10 --max-articles-per-source 1 --strategy rss --force-refresh --step-timeout-seconds 180` | **Exit 0** — profile + Scrapy RSS + export hoàn tất trong giới hạn từng bước |

### Latest `final_crawl_report.md` (sau pipeline trên)

File: `leon_web_intel/data/exports/final_crawl_report.md`

- **Run ID:** `6f6bfbea-c05d-49c7-b8d4-1e3df22cddcb` — status **success**
- **Articles:** 3  
- **Errors:** 17 (toàn bộ **AccessControlDetected** trong báo cáo)  
- **Frontier:** crawled **3**, skipped **14**, pending/crawling/failed **0**  
- **Discovered URLs (totals):** 0  

### Notes

- Subprocess timeout dùng `subprocess.run(..., timeout=...)` (Python kill child sau timeout). Export khôi phục chạy **`run_export.py`** không timeout để tối đa hóa khả năng ghi partial.
- Không thêm AI summary, dashboard, scheduler, proxy, stealth, bypass.

---

## Current session (2026-05-17) - E2E Crawl Foundation: runs, frontier, health, exports, report

### Current task

Leon: build a production-ready crawl foundation that can run small with `--limit` but has durable schema/pipeline foundations for larger later runs:

`sources_raw.txt -> profile -> crawl frontier -> Scrapy crawl -> articles/errors/source health -> exports -> final report`

### Files created

- `leon_web_intel/run_export.py` - exports articles/errors/discovered/frontier/source health plus final report.
- `leon_web_intel/run_pipeline.py` - subprocess orchestrator for profile, Scrapy, export; creates/finishes `crawl_runs`.
- `leon_web_intel/src/reporting/crawl_report.py` - `write_final_crawl_report(db, out_path)`.
- `leon_web_intel/tests/test_crawl_foundation.py` - offline tests for crawl runs, frontier, source health, exports, report, command building.

### Files modified

- `leon_web_intel/src/storage/db.py` - added tables `crawl_runs`, `crawl_frontier`, `source_health`; idempotent migration helper; crawl run helpers; frontier state helpers; source health recompute; article/error/discovered/frontier/health exports; crawl summary stats.
- `leon_web_intel/src/scrapy_engine/pipelines.py` - upsert frontier on item processing; mark successful article as `crawled`; mark fetch/extract errors as `failed`; mark duplicate/access-control/non-HTML skips as `skipped` where appropriate.
- `leon_web_intel/run_scrapy.py` - optional `--run-id`.
- `leon_web_intel/src/scrapy_engine/runner.py` - accepts optional `run_id` without coupling Scrapy internals to orchestration.
- `leon_web_intel/tests/conftest.py` - add repo root to `sys.path` so CLI helpers can be imported.
- `.github/workflows/leon_web_intel_ci.yml` - CI now runs `python -m pytest -v --tb=short`, profile dry-run, and `python run_export.py`; no network crawl.
- `leon_web_intel/README.md` - added "Production-ready E2E Crawl Foundation" flow, outputs, and scale/safety notes.
- `.ai/CURSOR_WORKLOG.md` - this entry.

### Schema added

- `crawl_runs`: run audit with input/config/status/totals/notes.
- `crawl_frontier`: URL state for pending/crawling/crawled/failed/skipped, retry count, last error, crawl timestamps, content hash.
- `source_health`: per-source URLs seen, inserted articles, errors, last success/error, success rate.

### Commands run

Interpreter used:

`D:\cursor\LEONCODE\CRAWL WEB\.tools\nuget_packages\python.3.11.9\tools\python.exe`

| Command | Result |
|---------|--------|
| `python -m pip install -r requirements.txt` | OK; requirements already satisfied |
| `python -m pytest -v --tb=short` | OK: 28 passed |
| `python run_profile.py --input config/sources_raw.txt --dry-run` | OK: 200 valid URLs, 198 unique sources |
| `python run_export.py` | OK: all export files written |
| `python run_pipeline.py --input config/sources_raw.txt --limit 10 --max-articles-per-source 2 --strategy all --force-refresh` | Timed out in Cursor shell after ~304s; subprocesses stopped; `crawl_runs` marked `failed` with timeout note |
| `python run_export.py` after timeout cleanup | OK: regenerated exports/report with failed run audit |

### Export files generated

- `leon_web_intel/data/exports/articles.csv`
- `leon_web_intel/data/exports/articles.parquet`
- `leon_web_intel/data/exports/crawl_errors.csv`
- `leon_web_intel/data/exports/discovered_urls.csv`
- `leon_web_intel/data/exports/crawl_frontier.csv`
- `leon_web_intel/data/exports/source_health.csv`
- `leon_web_intel/data/exports/final_crawl_report.md`

Final report after timeout cleanup recorded:

- latest run: `52cb53b0-b817-447f-8a0f-633a6359713f`, status `failed`
- sources: 10
- articles: 3
- errors: 13
- frontier crawled: 3
- frontier skipped: 13

### Failure / cleanup notes

`run_pipeline.py` timed out at the shell layer after ~5 minutes. The DB was locked by child Python processes:

- `run_pipeline.py --input config/sources_raw.txt --limit 10 ...`
- `run_scrapy.py --strategy all --limit 10 ... --run-id 52cb53b0-b817-447f-8a0f-633a6359713f`
- an older leftover `run_scrapy.py --strategy all --limit 5 --max-articles-per-source 2`

Stopped only Python processes whose command line matched `run_pipeline.py` or `run_scrapy.py`, then marked any `crawl_runs.status = 'running'` as `failed` with note:

`local agent timeout during run_pipeline smoke; subprocess stopped`

### Known limitations

- Local DuckDB only; no distributed scheduler.
- Scrapy crawl remains bounded by `--limit`, per-source caps, and CloseSpider timeout.
- No Redis/Celery/Airflow/dashboard/AI summary.
- No proxy rotation, stealth browser, CAPTCHA bypass, login automation, or paywall bypass.
- `run_pipeline.py` is architecturally wired, but full network E2E did not complete in this Cursor Windows agent within the timeout.

### Needs ChatGPT/Gemini review

- Review whether `ShortContent` should remain `failed` or be classified as `skipped` for frontier audit.
- Review future retry policy for `crawl_frontier.next_crawl_at` once a real scheduler is added.
- Review whether discovered RSS/sitemap URLs should be inserted into `discovered_urls` directly from Scrapy spiders in a later phase, beyond the current pipeline-level frontier integration.

---

Single shared AI workflow file — Leon, ChatGPT, Gemini ↔ Cursor.

---

## Current session (2026-05-17) — NuGet Python 3.11 on agent: pytest + profile OK; DuckDB migration + Scrapy runner fixes

### Current task

Leon: **ép chạy luôn**. Cài **Python 3.11.9** qua **NuGet** vào repo-local **`.tools/`** (đã **gitignore**), `pip install -r requirements.txt`, chạy **`pytest`**, **`run_profile.py`**, thử **`run_scrapy.py`**.

### Files modified

- `leon_web_intel/src/storage/db.py` — sau **`ALTER TABLE ... ADD COLUMN`** thất bại (cột đã có trong DDL), gọi **`ROLLBACK`** để DuckDB không để transaction **aborted** (fix **`insert_crawl_error`** / pipeline tests).
- `leon_web_intel/src/scrapy_engine/pipelines.py` — **`close_spider`**: **`self.db = None`** sau **`close()`**.
- `leon_web_intel/src/scrapy_engine/runner.py` — **`CrawlerProcess`** thay **`CrawlerRunner` + `reactor.run`**; **`ScrapyRunSummary.__copy__` / `__deepcopy__`** (Settings deepcopy không pickle **`threading.Lock`**).
- `leon_web_intel/src/scrapy_engine/settings.py` — **`CLOSESPIDER_TIMEOUT`** 600s; **`TWISTED_REACTOR`** = **`AsyncioSelectorReactor`** (Windows).
- `leon_web_intel/tests/test_scrapy_layer.py` — fixture **`yield`** kèm **`Settings`**; spider gắn **`settings`**; đóng pipeline trước khi **`duckdb.connect`**; **`HtmlResponse`** gắn **`Request`** cho **`meta`** (Scrapy 2.15).
- `.gitignore` — ignore **`.tools/`** (NuGet + Python cục bộ).

### Commands run (NuGet Python)

Interpreter:

`D:\cursor\LEONCODE\CRAWL WEB\.tools\nuget_packages\python.3.11.9\tools\python.exe`  
(`PYTHONPATH` = `leon_web_intel\src` cho CLI.)

| Command | Result |
|---------|--------|
| `python -m pytest -v --tb=short` | **22 passed** (~4s) |
| `python run_profile.py ... --dry-run` | **OK** — 198 unique sources |
| `python run_profile.py ... --profile-only --limit 10 --force-refresh` | **OK** (~101s) — ghi DuckDB + exports |
| `python run_scrapy.py --strategy rss --limit 1 ...` | **Treo >120s** trên agent Windows — log dừng sau pipeline init, **chưa thấy** `Spider opened` (môi trường/Cursor); **CI Linux** và máy Leon vẫn nên thử lại. |

### Known limitations

- **`run_scrapy`** chưa xác nhận end-to-end trên agent Windows; cần xác nhận trên **Linux Actions** hoặc máy local.

### Next suggested step

- Xem GitHub Actions sau push; local Windows: chạy **`run_scrapy`** với limit nhỏ nếu proxy/firewall khác agent.

---

## Current session (2026-05-16) — Run verification + GitHub CI

### Current task

Leon: **chạy thử** và **đưa kết quả lên GitHub**. Máy Cursor agent **không có Python** (`where python` rỗng, không tìm thấy `python.exe` trong repo hay path thường dùng), nên không chạy được `pytest` / CLI trực tiếp trên agent.

### Files created

- `.github/workflows/leon_web_intel_ci.yml` — GitHub Actions: **Ubuntu**, **Python 3.11**, `pip install -r leon_web_intel/requirements.txt`, **`python -m pytest -v --tb=short`**, **`python run_profile.py --input config/sources_raw.txt --dry-run`** (không HTTP). Kết quả xem tab **Actions** trên repo sau khi push.

### Files modified

- `.ai/CURSOR_WORKLOG.md` — mục session này.

### Commands run (Cursor agent)

```text
Get-Command python* → (empty)
Glob python.exe under workspace → 0 files
```

Không thể thực thi:

```bash
cd leon_web_intel && python -m pytest
```

### Test / CLI result

| Where | Result |
|-------|--------|
| Cursor agent shell | **Skipped** — không có interpreter |
| GitHub Actions | Chạy sau push; xem workflow **leon_web_intel CI** |

Profile có mạng / `run_scrapy` không đưa vào CI (tránh flaky / rate limit).

### Next suggested step

- Mở Actions trên GitHub sau push; trên máy local Leon chạy thêm `profile-only` và `run_scrapy` với limit nhỏ nếu cần.

---

## Current session (2026-05-16) — Scrapy layer runtime hardening (`_reserved` + pipeline teardown + offline HTML tests)

### Current task

Make Scrapy scaffold **safe to run**: cap **scheduled** HTTP requests for HTML spider (not only parsed items), close pipeline DB in pytest teardown, add **offline** unit tests; verify CLI `sys.path`; run pytest + smoke CLIs with **`python`** (not broken `py`).

### Files modified

- `leon_web_intel/src/scrapy_engine/spiders/html_article_spider.py` — add **`self._reserved`**. **`start_requests`**: init `_attempted`/`_reserved` to 0; schedule homepage only if `reserved < max`, then **`reserved += 1`** immediately. **`parse_page`**: return if `attempted >= max`; increment **`attempted`** and yield **`ArticleItem`**; return if `attempted >= max` before follows; child loop **`break`** when `reserved >= max`; increment **`reserved`** before each child **`Request`**.
- `leon_web_intel/tests/test_scrapy_layer.py` — **`pipeline_env`** is a **`yield`** fixture with **`finally: pipe.close_spider(...)`**; add **`test_html_article_spider_schedule_cap_no_network`** and **`test_html_article_spider_max_one_schedules_homepage_only`**.

### Files created / deleted

- *(none)*

### What was fixed (logic)

1. **`_reserved`** counts URLs **queued for download** as soon as **`Request` is yielded**, so the link-expand phase cannot schedule dozens of children before **`parse_page`** runs.
2. Pipeline tests release DuckDB after each test via **`close_spider`**.

### Commands run (Cursor agent)

Agent shell has **no `python` on PATH** and **no** interpreter at common install paths (see traceback below). Intended local commands:

```bash
cd leon_web_intel
python -m pip install -r requirements.txt
python -m pytest
python run_profile.py --input config/sources_raw.txt --dry-run
python run_profile.py --input config/sources_raw.txt --profile-only --limit 10 --force-refresh
python run_scrapy.py --strategy all --limit 5 --max-articles-per-source 2
```

### Test / CLI result (this environment)

- **`cmd /c where python`** → *(empty — no `python.exe` on PATH)*  
- Probed paths: `%LOCALAPPDATA%\Programs\Python\Python313\python.exe`, Python312, WindowsApps `python.exe`, `C:\Python313\python.exe` → **not present** on this runner.

**Leon:** install Python 3.11+ or add **`python.exe`** to PATH (or run with full path), fix **`py.ini`** if using launcher, then rerun the block above.

### Import path check

- **`run_profile.py`** / **`run_scrapy.py`**: both prepend **`leon_web_intel/src`** to **`sys.path`** before imports — run **`cd leon_web_intel`** then **`python run_*.py`** as documented.

### Known issues / limitations

- **`errback`** paths do not decrement **`reserved`** on failure (acceptable for this scaffold).
- Per-URL robots beyond Scrapy global obey unchanged.

### Notes for ChatGPT review

- Optional: align **`reserved`** with pipeline **`ShortContent`** retries (not in scope).

### Notes for Gemini review

- **`reserved`** vs **`attempted`** divergence when many responses fail — whether to allow “fill-up” scheduling later.

### Next suggested step

- Leon runs **`python -m pytest`** locally; then small **`run_scrapy`** smoke; commit/push.

---

## Previous session (2026-05-16) — Scrapy scaffold pre-flight patch (runtime + HTML cap + tests)

### Current task

Minimal fixes before **real** Scrapy runs: correct **ItemAdapter** import, **cap HTML spider** so `max_articles_per_source` stops both article attempts and link following, safer **www** stripping, **close DuckDB** in pipeline test fixture (Windows locks); run pytest + CLI smoke.

### Files modified

- `leon_web_intel/src/scrapy_engine/pipelines.py` — use **`from itemadapter import ItemAdapter`** (do **not** use `scrapy.ItemAdapter`; avoids runtime/type mismatch on some Scrapy builds).
- `leon_web_intel/src/scrapy_engine/spiders/html_article_spider.py` — early **return** when `self._attempted[sid] >= max_articles_per_source` (no item, no follows); re-check cap **before** scheduling each link and **after** depth gate; **`_host_key`**: `startswith("www.")` then `host = host[4:]` (no `lstrip("www.")`).
- `leon_web_intel/tests/test_scrapy_layer.py` — `WebIntelDB(db_path)` for schema init → **`.close()`** immediately so DuckDB file not locked when pipeline opens DB again.
- `leon_web_intel/requirements.txt` — explicit **`itemadapter>=0.7.0`** (direct import).

### Files created / deleted

- *(none)*

### What was fixed (logic)

1. **Pipeline:** `ItemAdapter` from **`itemadapter`** package — stable across Scrapy versions.
2. **HTML spider:** Article attempts and **child Request scheduling** both respect the same per-source cap (queued requests that wake after cap still **exit immediately** in `parse_page`).
3. **Host compare:** Only strips a single leading **`www.`**, avoids `lstrip("www.")` mangling hosts like `wwwtest.example`.
4. **Tests:** Fixture avoids holding two DuckDB handles on the same file on Windows.

### Commands run (Cursor agent)

```bash
cd leon_web_intel
python -m pytest
python run_profile.py --input config/sources_raw.txt --dry-run
python run_profile.py --input config/sources_raw.txt --profile-only --limit 10 --force-refresh
python run_scrapy.py --strategy all --limit 5 --max-articles-per-source 2
```

### Test / CLI result

- **`py -3.13 -m pytest`**: **FAILED to start** — launcher targets missing interpreter:

```
Unable to create process using 'D:\python.exe -m pytest -q': The system cannot find the file specified.
```

- **`run_profile.py` / `run_scrapy.py`**: **Not executed** here (same broken `py` → `D:\python.exe` binding).

Leon: fix Windows **`py.ini` / Python install path** (or run via full path to `python.exe`), then rerun the four commands locally and paste any new tracebacks.

### Known issues / limitations

- Unchanged: per-URL robots, reactor single-run semantics, approximate `requests_scheduled`.

### Notes for ChatGPT review

- Optional unit test: mock **HtmlArticleSpider.parse_page** queue depth vs cap (no network).

### Notes for Gemini review

- Whether **cap** should decrement on pipeline **rejection** (ShortContent) so HTML spider keeps trying more URLs until N successes — out of scope for this minimal patch.

### Next suggested step

- Leon runs **`pip install -r requirements.txt`** + **`pytest`** + bounded **`run_scrapy`** smoke; commit/push patch when satisfied.

---

## Previous session (2026-05-16) — Scrapy production crawl scaffold (Phase 3 prep)

### Scope

Add a **minimal Scrapy layer** under `leon_web_intel/src/scrapy_engine/` plus `run_scrapy.py`, wired **after** SourceProfiler (`best_strategy` in DuckDB). **No** profiler refactor; Scrapy is **not** a new peer strategy in the decision tree.

### Files created

- `leon_web_intel/run_scrapy.py` — CLI: `--strategy rss|sitemap|html|all`, `--limit`, `--max-articles-per-source`, `--db`.
- `leon_web_intel/src/scrapy_engine/__init__.py`
- `leon_web_intel/src/scrapy_engine/db_source_loader.py` — DuckDB `source_profiles` → RSS/sitemap/HTML buckets; skips `api_first`, `metadata_only`, `manual_review`, `playwright_fallback`; only `active` / `active_candidate`; HTML lane skips `robots_can_fetch_homepage = false`.
- `leon_web_intel/src/scrapy_engine/settings.py` — `build_scrapy_settings` / dict: `ROBOTSTXT_OBEY`, UA/timeout/retries/delay from `crawl_rules.yaml`, low per-domain concurrency, `COOKIES_ENABLED=False`, pipeline hook.
- `leon_web_intel/src/scrapy_engine/items.py` — `ArticleItem`.
- `leon_web_intel/src/scrapy_engine/extract_helpers.py` — keyword triplet + trafilatura helper (shared with pipeline).
- `leon_web_intel/src/scrapy_engine/pipelines.py` — DuckDB `articles` + `crawl_errors`; `AccessControlDetected` / `ShortContent` / fetch/http errors; duplicate `content_hash` skip (counter only); exceptions must not crash spider.
- `leon_web_intel/src/scrapy_engine/runner.py` — `CrawlerRunner` + sequential Twisted runs per lane; `ScrapyRunSummary`.
- `leon_web_intel/src/scrapy_engine/spiders/__init__.py`
- `leon_web_intel/src/scrapy_engine/spiders/rss_article_spider.py`
- `leon_web_intel/src/scrapy_engine/spiders/sitemap_article_spider.py`
- `leon_web_intel/src/scrapy_engine/spiders/html_article_spider.py`
- `leon_web_intel/tests/test_scrapy_layer.py` — loader filter, settings robots obey, pipeline access control + short content.

### Files modified

- `leon_web_intel/requirements.txt` — `scrapy>=2.11.0`.
- `leon_web_intel/README.md` — section **Scrapy production crawl layer** + flow `run_profile.py` → `run_scrapy.py`.

### Files deleted

- *(none)*

### What was implemented (logic)

1. **Separation:** SourceProfiler unchanged; Scrapy only consumes persisted `best_strategy` / URLs / robots homepage flag.
2. **Governance:** Robots obey on; paywall/login/CAPTCHA keywords before raw save → `crawl_errors` / no full article row; `min_article_content_length` → `ShortContent`; reuse `compute_quality_score` on successful inserts.
3. **Run model:** One reactor pass; spiders chained RSS → sitemap → HTML when `--strategy all`.

### How to run

```bash
cd leon_web_intel
python run_profile.py --input config/sources_raw.txt --dry-run
python run_profile.py --input config/sources_raw.txt --profile-only --limit 10 --force-refresh
python run_scrapy.py --strategy all --limit 5 --max-articles-per-source 2
```

### How to test

```bash
cd leon_web_intel
python -m pytest
python -m pytest tests/test_scrapy_layer.py -q
```

### Test result

- **`pytest`**: **Not executed successfully** in this Cursor runner (`py` → missing `D:\python.exe`). Leon should run locally after `pip install -r requirements.txt`.

### Known issues / limitations

- **Per-URL robots** (`can_fetch` on each article URL) not enforced here beyond Scrapy’s global `ROBOTSTXT_OBEY` + downstream policies.
- HTML spider is **shallow** (depth/link caps); sitemap nested fetch capped (`max_sitemap_nested`).
- **`requests_scheduled`** is an approximate counter from spiders, not Scrapy scheduler internals.

### Notes for ChatGPT review

- Whether Scrapy middleware should **mirror profiler HTTP cache** paths for repeatability.
- Whether duplicate-hash skips should optionally write a **`DuplicateContent`** crawl_errors row for audit.

### Notes for Gemini review

- Twisted **`reactor.run`** once per process vs subprocess-per-lane if Cursor users run multiple `run_scrapy` invocations in one long-lived REPL.

### Next suggested step

- Local pytest full suite + small `--limit` `run_scrapy` smoke against a known RSS domain.

---

## Previous session (2026-05-16) — safety / governance patches (robots, paywall, DuckDB lock)

### Scope (archived task)

Leon: **review & minimal patch** `leon_web_intel` — robots enforcement, paywall/article handling, DuckDB thread safety, tests, worklog — **no large refactor**, no real API adapters, no production crawl.

### Files created

- *(none)*

### Files modified

- `leon_web_intel/src/profiler/source_profiler.py` — `robots_can_fetch_homepage` on `SourceProfile`; skip homepage fetch + stub `HTMLProbeResult` when robots disallow; `apply_robots_homepage_governance()` downgrades `html_then_trafilatura` / `playwright_fallback` → `metadata_only` or `manual_review`; `crawl_errors` row `RobotsDisallowHomepage` when downgrade applies.
- `leon_web_intel/src/storage/db.py` — column `robots_can_fetch_homepage` in DDL + `ALTER` migration; **`threading.Lock`** around all `conn` usages + `fetch_distinct_content_hashes()`.
- `leon_web_intel/run_profile.py` — `existing_hashes()` via DB helper; `robots_allows_homepage_row()` guards metadata homepage fetch, HTML sample crawl, Playwright; **Playwright** path runs `detect_paywall_signals` before extract; **RSS/HTML extract loop**: skip `insert_article` + `AccessControlDetected` when paywall/login/captcha from `extract_article`.
- `leon_web_intel/src/extraction/article_extractor.py` — if paywall/login/captcha **before** saving raw HTML → return early (**no** `raw_store.save_html`, no trafilatura body extract).
- `leon_web_intel/tests/test_strategy_decision.py` — tests for robots downgrade (HTML, Playwright, RSS unchanged).
- `leon_web_intel/docs/data_contract.md` — document `robots_can_fetch_homepage`.

### Files deleted

- *(none)*

### What was implemented (logic)

1. **Robots:** Persist `robots_can_fetch_homepage` from `robots_checker.can_fetch_homepage`. Profiler **does not HTTP-fetch homepage** for RSS/HTML probe when disallowed. Strategies HTML/Playwright **downgraded** + reason in `error_message` + `crawl_errors`. Sample crawl respects stored flag for metadata/HTML/Playwright branches.
2. **Paywall/login/captcha:** No persisting full raw HTML on blocked articles; sample crawl logs **`AccessControlDetected`** at `extract` and skips article insert (Playwright uses keyword scan on rendered HTML).
3. **DuckDB:** Single shared connection serialized with one lock (acceptable minimal fix for `ThreadPoolExecutor` profiler).

### How to run

```bash
cd leon_web_intel
python run_profile.py --input config/sources_raw.txt --dry-run
python run_profile.py --input config/sources_raw.txt --profile-only --limit 10 --force-refresh
python run_profile.py --input config/sources_raw.txt --crawl-sample --max-articles-per-source 3 --limit 10
```

### How to test

```bash
cd leon_web_intel
python -m pytest
```

### Test result

- **`python -m pytest`**: **Not executed** in Cursor agent environment (`py` launcher points to missing `D:\python.exe` on this runner).
- **`run_profile.py --dry-run` / `--profile-only --limit 10 --force-refresh`**: **Not executed** (same).

Leon should run the three commands locally and paste any failure trace if needed.

### Known issues / limitations

- Robots enforcement for **RSS/sitemap/article URLs** in sample crawl is still **partial** (homepage gate + strategy downgrade; per-article `can_fetch` not yet enforced).
- Serialized DuckDB access may **slow** high concurrency; OK for v1 profiling scale.

### Risks

- Strict keyword blocking may increase **false-positive** `AccessControlDetected` on legitimate pages mentioning “subscribe”.

### Notes for ChatGPT review

- Whether to add **`can_fetch` per discovered URL** before RSS item/article GET.
- Whether **`metadata_only`** should still insert a **thin** article row (title/URL only) vs errors-only.

### Notes for Gemini review

- DuckDB **single-connection + lock** vs **connection-per-thread** tradeoff for future scale.

### Next suggested step

- Local **pytest + profile --limit 10**; optional CI workflow running pytest on push.

---

## Archive — auto Git sync policy (2026-05-16)

- Cursor rule: commit/push after substantive changes unless Leon opts out.

## Archive — charter alignment

- Tầng 0–11 mapping vs `leon_web_intel/` tree.
