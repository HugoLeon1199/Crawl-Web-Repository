from profiler.normalize import generate_source_id, normalize_url


def test_normalize_url_basic():
    n = normalize_url("https://www.bbc.com/news")
    assert n.domain == "bbc.com"
    assert n.source_id == "bbc_com"
    assert "bbc.com" in n.normalized_url


def test_normalize_url_scheme_default():
    n = normalize_url("vnexpress.net/")
    assert n.domain == "vnexpress.net"
    assert n.source_id == "vnexpress_net"


def test_generate_source_id():
    assert generate_source_id("SEC.GOV") == "sec_gov"
