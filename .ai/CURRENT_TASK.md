# Current Task

## Task Name

Build Universal Source Profiler v1

## Goal

Create the first working version of the source profiling system.

The system should read links from:

```text
config/sources_raw.txt
```

Then automatically detect:

- known API source
- RSS feed
- sitemap
- static HTML extraction ability
- JavaScript-heavy behavior
- paywall/login/CAPTCHA signals

Finally, it should assign `best_strategy` and save results.

## Input

```text
config/sources_raw.txt
```

## Output

```text
data/db/web_intel.duckdb
data/exports/source_profiles.csv
data/exports/source_profiles.parquet
data/exports/review_sources.csv
data/exports/profile_summary.md
logs/app.log
```

## Acceptance Criteria

- Dry run works.
- Profile-only mode works.
- Source profiles are saved.
- Review sources are exported.
- Summary report is generated.
- One bad source does not crash the whole run.
- No Playwright unless explicitly enabled.
- No CAPTCHA/paywall/login bypass.
- README and data contract are updated.

## Test Plan

Run:

```bash
python run_profile.py --input config/sources_raw.txt --dry-run
python run_profile.py --input config/sources_raw.txt --profile-only --limit 10
python run_profile.py --input config/sources_raw.txt --crawl-sample --max-articles-per-source 3 --limit 10
```
