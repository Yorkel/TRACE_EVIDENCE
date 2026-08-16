"""Offline unit tests for the shared robots.txt gate.

No network: the gate's fetcher is injected, so every case is deterministic. Covers
allow / disallow (including the declared product token) / crawl-delay /
fetch-failure-fails-closed, plus the one-fetch-per-host cache.

Run with: pytest tests/test_robots_gate.py -v
"""
from trace_evidence.robots import RobotsGate


ALLOW_ALL = "User-agent: *\nAllow: /\n"
DISALLOW_NEWS = "User-agent: *\nDisallow: /private/\n"
# Rule targeted specifically at the declared product token.
TRACE_BLOCKED = (
    "User-agent: TRACEEvidenceBot\nDisallow: /news/\n\n"
    "User-agent: *\nAllow: /\n"
)
CRAWL_DELAY = "User-agent: *\nCrawl-delay: 7\nDisallow:\n"


def _gate(status_code, text=""):
    return RobotsGate(fetcher=lambda url: (status_code, text))


def _gate_raising():
    def boom(url):
        raise OSError("network down")
    return RobotsGate(fetcher=boom)


class TestAllow:
    def test_wildcard_allow(self):
        g = _gate(200, ALLOW_ALL)
        assert g.can_fetch("https://example.org/news/article-1") is True

    def test_no_robots_txt_allows(self):
        # A clean 404 means "no robots.txt here" -> crawling permitted (RFC 9309).
        g = _gate(404, "")
        assert g.can_fetch("https://example.org/anything") is True
        assert g.status("https://example.org/anything") == "absent"


class TestDisallow:
    def test_disallowed_path(self):
        g = _gate(200, DISALLOW_NEWS)
        assert g.can_fetch("https://example.org/private/secret") is False
        assert g.can_fetch("https://example.org/public/page") is True

    def test_rule_matches_our_real_useragent_token(self):
        g = _gate(200, TRACE_BLOCKED)
        # The TRACE-specific block applies to us...
        assert g.can_fetch("https://example.org/news/x") is False
        # ...but non-disallowed paths are still allowed.
        assert g.can_fetch("https://example.org/research/y") is True


class TestCrawlDelay:
    def test_crawl_delay_parsed(self):
        g = _gate(200, CRAWL_DELAY)
        assert g.crawl_delay("https://example.org/") == 7
        # Crawl-delay does not by itself forbid fetching.
        assert g.can_fetch("https://example.org/page") is True

    def test_no_crawl_delay_is_none(self):
        g = _gate(200, ALLOW_ALL)
        assert g.crawl_delay("https://example.org/") is None


class TestFailClosed:
    def test_network_failure_fails_closed(self):
        g = _gate_raising()
        assert g.can_fetch("https://example.org/anything") is False
        assert g.status("https://example.org/anything") == "blocked"

    def test_5xx_fails_closed(self):
        g = _gate(503, "")
        assert g.can_fetch("https://example.org/") is False
        assert g.status("https://example.org/") == "blocked"

    def test_non_404_4xx_fails_closed(self):
        g = _gate(429, "")
        assert g.can_fetch("https://example.org/") is False
        assert g.status("https://example.org/") == "blocked"

    def test_robots_access_forbidden_fails_closed(self):
        # 401/403 on robots.txt itself -> we can't read the rules -> disallow.
        g = _gate(403, "")
        assert g.can_fetch("https://example.org/") is False

    def test_missing_host_fails_closed(self):
        g = _gate(200, ALLOW_ALL)
        assert g.can_fetch("not-a-url") is False


class TestOverride:
    def test_override_unblocks_a_disallowed_host(self):
        g = _gate(200, "User-agent: *\nDisallow: /\n")
        assert g.can_fetch("https://example.org/news") is False
        g.add_override("https://example.org/news")
        assert g.can_fetch("https://example.org/anything") is True  # host-wide
        assert g.is_override("https://example.org/x") is True

    def test_override_is_per_host(self):
        g = _gate(200, "User-agent: *\nDisallow: /\n")
        g.add_override("https://a.org/")
        assert g.can_fetch("https://a.org/x") is True
        assert g.can_fetch("https://b.org/x") is False  # other hosts still blocked

    def test_scoped_override_is_per_path(self):
        g = _gate(200, "User-agent: *\nDisallow: /\n")
        g.add_override("https://example.org/sitemap.xml", path_pattern=r"^/news/[^?]+$")
        assert g.can_fetch("https://example.org/news/article-1/") is True
        assert g.can_fetch("https://example.org/news/?cat=filter") is False
        assert g.can_fetch("https://example.org/search/") is False


class TestPermissiveRobots:
    """A 200 robots.txt with no applicable rules means allow-all (RFC 9309).
    Regression for the gate wrongly fail-closing empty / sitemap-only files."""

    def test_empty_robots_allows(self):
        # nicie.org serves a 0-byte robots.txt -> no rules -> crawl permitted.
        g = _gate(200, "")
        assert g.can_fetch("https://example.org/wp-json/wp/v2/posts") is True
        assert g.status("https://example.org/") == "ok"

    def test_sitemap_only_robots_allows(self):
        # gtcs/asti serve only a Sitemap: line (no User-agent group) -> allow-all.
        g = _gate(200, "Sitemap: https://example.org/sitemap.xml\n")
        assert g.can_fetch("https://example.org/news") is True

    def test_comment_only_robots_allows(self):
        g = _gate(200, "# nothing to see here\n")
        assert g.can_fetch("https://example.org/x") is True

    def test_bom_prefixed_robots_parses(self):
        # holyrood.com serves a UTF-8 BOM; after stripping it the rule must apply.
        g = _gate(200, "﻿User-agent: *\nDisallow: /\n")
        assert g.can_fetch("https://example.org/x") is False

    def test_html_masquerading_as_robots_fails_closed(self):
        # A captcha/SPA page served with 200 is NOT a robots.txt -> fail closed.
        g = _gate(200, "<!DOCTYPE html>\n<html><body>Just a moment...</body></html>")
        assert g.can_fetch("https://example.org/") is False
        assert g.status("https://example.org/") == "blocked"


class TestCache:
    def test_one_fetch_per_host(self):
        calls = []

        def counting_fetcher(url):
            calls.append(url)
            return (200, ALLOW_ALL)

        g = RobotsGate(fetcher=counting_fetcher)
        g.can_fetch("https://example.org/a")
        g.can_fetch("https://example.org/b")
        g.crawl_delay("https://example.org/c")
        g.status("https://example.org/d")
        assert len(calls) == 1  # robots.txt fetched once, then cached

    def test_distinct_hosts_fetched_separately(self):
        calls = []

        def counting_fetcher(url):
            calls.append(url)
            return (200, ALLOW_ALL)

        g = RobotsGate(fetcher=counting_fetcher)
        g.can_fetch("https://a.org/x")
        g.can_fetch("https://b.org/x")
        assert len(calls) == 2
