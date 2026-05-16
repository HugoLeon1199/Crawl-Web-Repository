from profiler.source_profiler import SourceProfile, decide_best_strategy
from settings import CrawlRules


def rules() -> CrawlRules:
    return CrawlRules()


def test_strategy_known_api_wins_over_rss():
    p = SourceProfile(
        has_known_api=True,
        has_rss=True,
        rss_valid_count=2,
        has_sitemap=True,
        sitemap_url_count=1,
        html_extract_ok=True,
        html_status_code=200,
    )
    decide_best_strategy(p, rules())
    assert p.best_strategy == "api_first"


def test_strategy_rss_before_sitemap():
    p = SourceProfile(
        has_known_api=False,
        has_rss=True,
        rss_valid_count=1,
        has_sitemap=True,
        sitemap_url_count=3,
        html_extract_ok=False,
        html_status_code=200,
    )
    decide_best_strategy(p, rules())
    assert p.best_strategy == "rss_then_article_extract"


def test_strategy_paywall_gate():
    p = SourceProfile(
        has_known_api=False,
        has_rss=False,
        rss_valid_count=0,
        has_sitemap=False,
        sitemap_url_count=0,
        html_extract_ok=False,
        html_status_code=200,
        js_required=False,
        paywall_detected=True,
    )
    decide_best_strategy(p, rules())
    assert p.best_strategy == "metadata_only"
