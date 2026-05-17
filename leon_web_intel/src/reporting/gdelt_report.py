"""Markdown summary for a GDELT DOC fetch run."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


def write_today_gdelt_report(
    out_path: Path,
    *,
    target_calendar_date: str,
    timezone_name: str,
    utc_window: tuple[datetime, datetime],
    query: str,
    total_hits: int,
    extracted_ok: int,
    extract_errors: int,
    argv: list[str],
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    start_u, end_u = utc_window
    cmd = " ".join(argv)
    lines = [
        "# GDELT Today Report",
        "",
        "## Target",
        f"- Calendar date: **{target_calendar_date}**",
        f"- Timezone: **{timezone_name}**",
        f"- UTC window: `{start_u}` → `{end_u}`",
        f"- Query: `{query}`",
        "",
        "## Totals",
        f"- **GDELT ArtList rows stored:** {total_hits}",
        f"- **Articles extracted (success):** {extracted_ok}",
        f"- **Extract failures / skips:** {extract_errors}",
        "",
        "## Command",
        f"- `{cmd}`",
        "",
        "## Notes",
        "- DOC API maxes at 250 records per HTTP request; time-window tiling + bisection reduces truncation.",
        "- No paywall/login/captcha bypass; failures recorded per URL.",
        "",
    ]
    out_path.write_text("\n".join(lines), encoding="utf-8")
