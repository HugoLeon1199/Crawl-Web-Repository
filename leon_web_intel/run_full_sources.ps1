# Full pipeline: profile ALL seeds from config/sources_raw.txt (force refresh),
# then sample crawl up to sample_max (override via --max-articles-per-source).
# Uses Python 3.12 if default py launcher points to a broken path.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$Py = "C:\Program Files\Python312\python.exe"
if (-not (Test-Path $Py)) { $Py = "python" }

& $Py run_profile.py `
  --input config/sources_raw.txt `
  --crawl-sample `
  --max-articles-per-source 10000 `
  --force-refresh `
  --with-playwright

Write-Host "`nWhen finished, run coverage report:" -ForegroundColor Cyan
Write-Host "  & `"$Py`" run_source_file_coverage.py" -ForegroundColor Cyan
