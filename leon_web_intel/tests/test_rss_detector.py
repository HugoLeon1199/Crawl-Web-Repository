from profiler.rss_detector import parse_rss_candidate


def test_parse_rss_candidate_valid():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0"><channel><title>T</title>
    <item><title>Hello</title><link>https://example.com/x</link></item>
    </channel></rss>"""
    assert parse_rss_candidate(xml, "https://example.com/feed") is True


def test_parse_rss_candidate_invalid():
    assert parse_rss_candidate("<html><body>nope</body></html>", "u") is False
