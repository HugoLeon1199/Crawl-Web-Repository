"""Packaged entry — forwards to repository-level CLI."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    rp = root / "run_profile.py"
    spec = importlib.util.spec_from_file_location("run_profile", rp)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load run_profile.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    raise SystemExit(module.main())


if __name__ == "__main__":
    main()
