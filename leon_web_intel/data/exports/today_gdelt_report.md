# GDELT Today Report

## Target
- Calendar date: **2026-05-17**
- Timezone: **Europe/Amsterdam**
- UTC window: `2026-05-16 22:00:00+00:00` → `2026-05-17 22:00:00+00:00`
- Query: `(see gdelt run / api_query column in CSV)`

## Totals
- **GDELT ArtList rows stored:** 0
- **Articles extracted (success):** 0
- **Extract failures / skips:** 0

## Command
- `run_export.py --today-only --date today --timezone Europe/Amsterdam`

## Notes
- DOC API maxes at 250 records per HTTP request; time-window tiling + bisection reduces truncation.
- No paywall/login/captcha bypass; failures recorded per URL.
