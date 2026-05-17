"""CLI resolution helpers for full-run caps."""

from __future__ import annotations

from utils.full_run import FULL_RUN_URL_CAP_PER_SOURCE, profile_limit_arg, resolve_max_urls_per_source


def test_resolve_max_urls_zero() -> None:
    assert resolve_max_urls_per_source(0) == FULL_RUN_URL_CAP_PER_SOURCE
    assert resolve_max_urls_per_source(-1) == FULL_RUN_URL_CAP_PER_SOURCE


def test_profile_limit_arg() -> None:
    assert profile_limit_arg(0) is None
    assert profile_limit_arg(-3) is None
    assert profile_limit_arg(12) == 12
