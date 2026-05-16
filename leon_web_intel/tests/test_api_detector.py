from pathlib import Path

import pytest

from profiler.api_detector import detect_known_api
from settings import load_known_api_config


@pytest.fixture()
def known_cfg(tmp_path: Path):
    p = tmp_path / "k.yaml"
    p.write_text(
        """
known_api_adapters:
  sec:
    domains:
      - sec.gov
    adapter: sec_edgar_collector
    endpoint_hint: https://www.sec.gov/
""",
        encoding="utf-8",
    )
    return load_known_api_config(p)


def test_detect_known_api_direct(known_cfg):
    hit = detect_known_api("sec.gov", known_cfg)
    assert hit is not None
    assert hit.entry.adapter == "sec_edgar_collector"


def test_detect_known_api_subdomain(known_cfg):
    hit = detect_known_api("www.sec.gov", known_cfg)
    assert hit is not None


def test_detect_known_api_miss(known_cfg):
    assert detect_known_api("example.com", known_cfg) is None
