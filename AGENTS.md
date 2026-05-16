# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

Leon Global Web Intelligence Engine — a Python CLI pipeline that profiles web sources and runs lightweight sample crawls. Pure Python, no Docker, no external services. See `leon_web_intel/README.md` for full documentation.

### Development environment

- **Python 3.12** with a virtual environment at `leon_web_intel/.venv`
- Activate: `source leon_web_intel/.venv/bin/activate`
- All commands run from `leon_web_intel/` directory

### Running tests

```bash
cd leon_web_intel && source .venv/bin/activate && python -m pytest -v
```

All 16 tests are pure unit tests with no network or DB dependency.

### Running the application

```bash
cd leon_web_intel && source .venv/bin/activate

# Dry run (no network, no DB)
python run_profile.py --input config/sources_raw.txt --dry-run

# Profile sources (requires network)
python run_profile.py --input config/sources_raw.txt --profile-only --limit 5

# Sample crawl (requires network)
python run_profile.py --input config/sources_raw.txt --crawl-sample --max-articles-per-source 3 --limit 5
```

### Known issue: DuckDB transaction bug

The `WebIntelDB.__init__` in `src/storage/db.py` executes multi-statement DDL followed by an `ALTER TABLE` migration that fails (column already exists on fresh DBs). The failed ALTER leaves DuckDB's implicit transaction in an aborted state, causing all subsequent writes (upsert, insert) to fail with `TransactionContext Error: Current transaction is aborted (please ROLLBACK)`. The profiling **logic** works correctly (strategies are determined and logged), but results are not persisted to DuckDB and the export step crashes. This is a pre-existing code bug, not an environment issue.

### No linter configured

The repository does not include a linter configuration (no `ruff.toml`, `pyproject.toml`, `.flake8`, etc.). There is no lint script in the project.

### Dependencies

`python3.12-venv` system package is required to create the virtual environment. All Python dependencies are in `leon_web_intel/requirements.txt`.
