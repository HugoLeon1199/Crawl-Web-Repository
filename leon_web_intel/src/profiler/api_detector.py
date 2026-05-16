"""Match domains against configured known API adapters."""

from __future__ import annotations

from dataclasses import dataclass

from settings import KnownAdapterEntry, KnownApiConfig, flatten_known_domains


@dataclass
class KnownApiMatch:
    adapter_key: str
    entry: KnownAdapterEntry


def detect_known_api(domain: str, cfg: KnownApiConfig) -> KnownApiMatch | None:
    flat = flatten_known_domains(cfg)
    canon = domain.lower().strip(".")
    if canon.startswith("www."):
        canon = canon[4:]
    if canon in flat:
        key, entry = flat[canon]
        return KnownApiMatch(adapter_key=key, entry=entry)
    # suffix match for subdomains e.g. news.sec.gov -> sec.gov
    parts = canon.split(".")
    for i in range(len(parts)):
        cand = ".".join(parts[i:])
        if cand in flat:
            key, entry = flat[cand]
            return KnownApiMatch(adapter_key=key, entry=entry)
    return None
