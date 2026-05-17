"""Governance: refined AccessControlDetected vs public HTML chrome."""

from __future__ import annotations

from scrapy_engine.extract_helpers import access_control_triplet, extract_with_trafilatura

# Mirrors ``config/crawl_rules.yaml`` subsets used in pipeline tests.
_PAY = [
    "subscribe",
    "subscription",
    "premium",
    "sign in to continue",
    "login to continue",
    "register to read",
    "paywall",
    "captcha",
    "access denied",
    "forbidden",
    "cloudflare",
    "verify you are human",
]
_LOGIN = ["sign in", "log in", "login", "register to read"]
_CAP = ["captcha", "verify you are human", "recaptcha"]


def test_public_article_subscribe_nav_long_body_not_blocked() -> None:
    article = "<p>" + ("Public article sentence. " * 80) + "</p>"
    html = f"<html><body><header>Subscribe</header><main>{article}</main></body></html>"
    ext = extract_with_trafilatura(html)
    p, l, c = access_control_triplet(
        html,
        _PAY,
        _LOGIN,
        _CAP,
        extracted_plain=ext.content or "",
        content_length=ext.content_length,
        min_article_content_length=300,
    )
    assert ext.content_length >= 300
    assert (p, l, c) == (False, False, False)


def test_paywall_subscribe_to_continue_short_blocked() -> None:
    html = "<html><body><p>Subscribe to continue reading</p><p>x</p></body></html>"
    ext = extract_with_trafilatura(html)
    p, l, c = access_control_triplet(
        html,
        _PAY,
        _LOGIN,
        _CAP,
        extracted_plain=ext.content or "",
        content_length=ext.content_length,
        min_article_content_length=300,
    )
    assert p or l
    assert c is False


def test_captcha_verify_human_blocked() -> None:
    html = "<html><body><main>verify you are human before continuing</main></body></html>"
    ext = extract_with_trafilatura(html)
    p, l, c = access_control_triplet(
        html,
        _PAY,
        _LOGIN,
        _CAP,
        extracted_plain=ext.content or "",
        content_length=ext.content_length,
        min_article_content_length=300,
    )
    assert c is True


def test_login_to_continue_blocked() -> None:
    html = "<html><body><div>Please login to continue</div></body></html>"
    ext = extract_with_trafilatura(html)
    p, l, c = access_control_triplet(
        html,
        _PAY,
        _LOGIN,
        _CAP,
        extracted_plain=ext.content or "",
        content_length=ext.content_length,
        min_article_content_length=300,
    )
    assert l is True
    assert c is False
