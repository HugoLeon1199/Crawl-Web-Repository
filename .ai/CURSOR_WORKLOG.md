# CURSOR_WORKLOG — shared worklog

**Repo:** https://github.com/HugoLeon1199/Crawl-Web-Repository  
**Project:** Leon Global Web Intelligence Engine  

Single shared AI workflow file — Leon, ChatGPT, Gemini ↔ Cursor.

---

## Current session (2026-05-16) — safety / governance patches (robots, paywall, DuckDB lock)

### Current task

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
