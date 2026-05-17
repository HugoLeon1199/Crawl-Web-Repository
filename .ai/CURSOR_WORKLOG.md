# CURSOR_WORKLOG — shared worklog

**Repo:** https://github.com/HugoLeon1199/Crawl-Web-Repository  
**Project:** Leon Global Web Intelligence Engine  

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
