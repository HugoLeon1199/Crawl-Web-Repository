"""Markdown summary for API Hub runs."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def write_today_api_report(
    path: Path,
    *,
    target_calendar_date: str,
    timezone_name: str,
    window_start_utc: Any,
    window_end_utc: Any,
    counts_by_adapter: dict[str, int],
    extracted_fulltext_n: int,
    api_errors_by_adapter: dict[str, int],
    argv: list[str],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    total = int(sum(counts_by_adapter.values()))
    lines = [
        "# Today API Hub Report",
        "",
        "## Target",
        f"- Calendar date: **{target_calendar_date}**",
        f"- Timezone: **{timezone_name}**",
        f"- UTC window: `{window_start_utc}` → `{window_end_utc}`",
        "",
        "## Record counts by adapter",
        _fmt_counts(counts_by_adapter),
        "",
        "## Totals",
        f"- **Total API metadata rows (window):** {total}",
        f"- **Full-text extracts (strategy api_trafilatura_extract, window):** {extracted_fulltext_n}",
        "",
        "## API Hub errors by adapter",
        _fmt_counts(api_errors_by_adapter),
        "",
        "## Command",
        "",
        "```",
        " ".join(argv),
        "```",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _fmt_counts(values: dict[str, int]) -> str:
    if not values:
        return "- *(none)*"
    parts = [f"- **{k}:** {v}" for k, v in sorted(values.items(), key=lambda kv: (-kv[1], kv[0]))]
    return "\n".join(parts)
