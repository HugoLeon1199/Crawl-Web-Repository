# Today-only stats: intersection of classified IDs (CSV) x DuckDB articles x source_profiles.
$Py = "C:\Program Files\Python312\python.exe"
if (-not (Test-Path $Py)) { $Py = "python" }
Set-Location $PSScriptRoot

& $Py run_classified_sources_weekly_article_counts.py `
  --window today `
  --timezone Europe/Amsterdam `
  --classified-csv "data/exports/source_profiles.csv" `
  --metric extracted `
  --md-out "data/exports/articles_today_by_classified_source.md" `
  --csv-out "data/exports/articles_today_by_classified_source.csv"
