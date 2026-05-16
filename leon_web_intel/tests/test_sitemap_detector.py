from profiler.sitemap_detector import parse_sitemap_bytes


def test_parse_sitemap_urlset():
    body = b"""<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>https://news.example.com/2024/article-1</loc></url>
      <url><loc>https://news.example.com/2024/article-2</loc></url>
    </urlset>"""
    ok, urls, is_index = parse_sitemap_bytes(body, "https://example.com/sitemap.xml")
    assert ok
    assert not is_index
    assert len(urls) == 2


def test_parse_sitemap_index():
    body = b"""<?xml version="1.0" encoding="UTF-8"?>
    <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <sitemap><loc>https://example.com/sitemap-1.xml</loc></sitemap>
    </sitemapindex>"""
    ok, urls, is_index = parse_sitemap_bytes(body, "https://example.com/sitemap_index.xml")
    assert ok
    assert is_index
    assert urls
