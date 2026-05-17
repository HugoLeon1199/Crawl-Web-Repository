"""Ordered registry of API adapters for TODAY GLOBAL INTELLIGENCE ENGINE."""

from __future__ import annotations

from collectors.api_adapters.arxiv import ArxivAdapter
from collectors.api_adapters.base import ApiAdapter
from collectors.api_adapters.crossref import CrossrefAdapter
from collectors.api_adapters.gdelt import GdeltAdapter
from collectors.api_adapters.github_api import GitHubApiAdapter
from collectors.api_adapters.openalex import OpenAlexAdapter
from collectors.api_adapters.pubmed import PubMedAdapter
from collectors.api_adapters.sec_edgar import SecEdgarAdapter
from collectors.api_adapters.semantic_scholar import SemanticScholarAdapter
from collectors.api_adapters.world_bank import WorldBankAdapter

_ADAPTER_ORDER: list[tuple[str, type[ApiAdapter]]] = [
    ("gdelt", GdeltAdapter),
    ("openalex", OpenAlexAdapter),
    ("arxiv", ArxivAdapter),
    ("sec", SecEdgarAdapter),
    ("world_bank", WorldBankAdapter),
    ("pubmed", PubMedAdapter),
    ("github", GitHubApiAdapter),
    ("crossref", CrossrefAdapter),
    ("semantic_scholar", SemanticScholarAdapter),
]

_NAME_TO_CLASS: dict[str, type[ApiAdapter]] = dict(_ADAPTER_ORDER)


def default_adapter_names() -> list[str]:
    return [name for name, _ in _ADAPTER_ORDER]


def resolve_adapter_names(spec: str) -> list[ApiAdapter]:
    """CLI ``all`` or comma-separated adapter keys (e.g. ``gdelt,pubmed``)."""
    s = (spec or "").strip().lower()
    if s == "all":
        return [cls() for _, cls in _ADAPTER_ORDER]
    out: list[ApiAdapter] = []
    for part in s.split(","):
        key = part.strip().lower()
        if not key:
            continue
        cls = _NAME_TO_CLASS.get(key)
        if cls is None:
            raise ValueError(f"unknown API adapter {key!r}; known: {', '.join(default_adapter_names())}")
        out.append(cls())
    return out
