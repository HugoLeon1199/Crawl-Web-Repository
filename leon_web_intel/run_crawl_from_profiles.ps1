# Crawl sample using ONLY existing rows in source_profiles (no HTTP profiler pass).
# Tune --max-articles-per-source (50–200 typical daily; 500 aggressive).
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$Py = "C:\Program Files\Python312\python.exe"
if (-not (Test-Path $Py)) { $Py = "python" }

& $Py run_profile.py `
  --input config/sources_raw.txt `
  --crawl-sample `
  --skip-profiling `
  --max-articles-per-source 150 `
  --with-playwright

Write-Host "`nCoverage:" -ForegroundColor Cyan
Write-Host "  & `"$Py`" run_source_file_coverage.py" -ForegroundColor Cyan
