"""Shared, fail-closed robots.txt gate for every network fetch path.

Network adapters can route fetch decisions through this shared gate and record the
resulting ``robots_status`` in their run manifests.

Design rules (research-ethics requirements, deliberately conservative):

* **One fetch + cache of each host's robots.txt per process** (= per run). The
  module-level singleton ``_GATE`` holds the cache; a fresh ``RobotsGate()`` (used
  by the tests) starts empty.
* **Matching uses the explicit product token ``TRACEEvidenceBot/1.0``** rather
  than inheriting an adapter's unrelated browser header.
* **Crawl-delay is honoured.** ``crawl_delay(url)`` exposes the parsed value and
  ``wait(url)`` spaces successive fetches to the same host by at least that delay.
* **FAIL CLOSED.** If robots.txt cannot be fetched or understood — network error,
  timeout, 5xx, 401/403, non-404 4xx, or unparseable — the host is treated as
  DISALLOWED. Only a clean "no robots.txt here" (404) is treated as
  "no restrictions", per the universal RFC 9309 convention. We never default to
  *allow* on uncertainty.
"""

import re
import threading
import time
from urllib import robotparser
from urllib.parse import urlsplit, urlunsplit

import requests

# The real product token we obey robots rules as. urllib reduces a User-Agent to
# the part before the first "/" and lowercases it, so this matches a robots
# the declared product-token line (and the wildcard entry).
USER_AGENT = "TRACEEvidenceBot/1.0"
ROBOTS_TIMEOUT = 15
_FETCH_HEADERS = {"User-Agent": USER_AGENT}


def _default_fetcher(robots_url, timeout=ROBOTS_TIMEOUT):
    """Fetch robots.txt → ``(status_code, text)``.

    Raises on any network failure; the gate turns every exception into a
    fail-closed (DISALLOW) verdict. Injectable so the unit test stays offline.
    """
    r = requests.get(robots_url, headers=_FETCH_HEADERS, timeout=timeout)
    return r.status_code, r.text


class _HostRules:
    """Cached robots verdict for one (scheme, host).

    ``status`` is one of:
      ``ok``      — robots.txt fetched and parsed; defer to the parser.
      ``absent``  — no robots.txt (clean 404 / 4xx-not-found) → crawling allowed.
      ``blocked`` — could not be fetched/understood → fail closed (DISALLOW all).
    """

    __slots__ = ("status", "_parser", "delay")

    def __init__(self, status, parser=None, delay=None):
        self.status = status
        self._parser = parser
        self.delay = delay

    def can_fetch(self, url, user_agent):
        if self.status == "blocked":
            return False
        if self.status == "absent":
            return True
        return self._parser.can_fetch(user_agent, url)


class RobotsGate:
    """Per-process robots cache. ``fetcher`` is injectable for offline tests."""

    def __init__(self, fetcher=_default_fetcher, user_agent=USER_AGENT):
        self._fetcher = fetcher
        self.user_agent = user_agent
        self._cache = {}        # (scheme, netloc) -> _HostRules
        self._last_fetch = {}   # (scheme, netloc) -> monotonic timestamp
        self._override = {}     # netloc -> list of compiled path/query regexes, or None for host-wide
        self._lock = threading.Lock()

    @staticmethod
    def _key(url):
        p = urlsplit(url)
        return (p.scheme or "https", p.netloc)

    @staticmethod
    def _robots_url(url):
        p = urlsplit(url)
        return urlunsplit((p.scheme or "https", p.netloc, "/robots.txt", "", ""))

    def _rules_for(self, url):
        key = self._key(url)
        if not key[1]:
            return _HostRules("blocked")  # no host → can't verify → fail closed
        with self._lock:
            cached = self._cache.get(key)
        if cached is not None:
            return cached
        rules = self._load(url)
        with self._lock:
            # Another thread may have loaded it meanwhile; first write wins.
            rules = self._cache.setdefault(key, rules)
        return rules

    def _load(self, url):
        try:
            status_code, text = self._fetcher(self._robots_url(url))
        except Exception:
            return _HostRules("blocked")            # fetch failure → fail closed
        if status_code == 200:
            # Strip a leading UTF-8 BOM: some hosts (e.g. holyrood.com) serve one,
            # and it corrupts the first directive line for robotparser.
            text = (text or "").lstrip("﻿")
            # A successfully-served robots.txt with no rules means "allow all"
            # (RFC 9309): empty bodies and sitemap-only / comment-only files are
            # valid and permissive — robotparser yields allow-all for them. But some
            # hosts serve an HTML error/captcha/SPA page with a 200 status; that is
            # NOT a robots.txt, so reject it (fail closed). We detect that by the
            # presence of HTML markup, not by requiring a User-agent line (which
            # wrongly blocked legitimately-empty and sitemap-only robots files).
            if re.search(r"<\s*(?:!doctype|html|head|body|script)\b", text, re.I):
                return _HostRules("blocked")        # HTML masquerading as robots → fail closed
            lines = text.splitlines()
            rp = robotparser.RobotFileParser()
            try:
                rp.parse(lines)
            except Exception:
                return _HostRules("blocked")        # unparseable → fail closed
            rp.modified()                            # ensure last_checked is set
            delay = rp.crawl_delay(self.user_agent)
            return _HostRules("ok", parser=rp,
                              delay=float(delay) if delay is not None else None)
        if status_code in (401, 403):
            return _HostRules("blocked")            # robots itself access-restricted
        if status_code == 404:
            return _HostRules("absent")             # clean no robots.txt → allowed
        return _HostRules("blocked")                # 5xx / unexpected → fail closed

    # ── public API ───────────────────────────────────────────────────────────
    def add_override(self, url, path_pattern=None):
        """Explicitly authorise a host despite robots (a human decision).

        Use ONLY for sources where a person has decided to proceed — e.g. a public
        open-data API whose robots.txt is merely erroring, or a site whose Disallow
        is an over-broad match of its real intent. Pass ``path_pattern`` to scope the
        override to a regex over path+query; omitting it remains host-wide for legacy
        tests/dev use. Overrides are recorded as ``robots_status: override`` in the
        manifest, never silent.
        """
        nl = urlsplit(url).netloc
        if nl:
            if path_pattern:
                self._override.setdefault(nl, []).append(re.compile(path_pattern))
            else:
                self._override[nl] = None

    def is_override(self, url):
        p = urlsplit(url)
        rules = self._override.get(p.netloc, False)
        if rules is False:
            return False
        if rules is None:
            return True
        target = p.path + (f"?{p.query}" if p.query else "")
        return any(rule.search(target) for rule in rules)

    def can_fetch(self, url):
        """True iff TRACEEvidenceBot/1.0 may fetch ``url`` (fail-closed),
        OR the host has an explicit human override registered via add_override."""
        if self.is_override(url):
            return True
        return self._rules_for(url).can_fetch(url, self.user_agent)

    def get(self, url, **kwargs):
        """Robots-gated requests.get for hand-written scrapers.

        Returns a Response on an allowed, successful HTTP attempt; returns None when
        robots disallows the URL or when the request itself fails. Callers still
        decide what HTTP status codes mean for their source.
        """
        if not self.can_fetch(url):
            return None
        self.wait(url)
        try:
            return requests.get(url, **kwargs)
        except requests.RequestException:
            return None

    def crawl_delay(self, url):
        """Host Crawl-delay in seconds (float), or None if unset/unavailable."""
        return self._rules_for(url).delay

    def status(self, url):
        """Host-level robots outcome for the manifest: ok | absent | blocked."""
        return self._rules_for(url).status

    def wait(self, url):
        """Sleep enough to honour the host Crawl-delay since its last fetch."""
        delay = self.crawl_delay(url)
        if not delay:
            return
        key = self._key(url)
        last = self._last_fetch.get(key)
        now = time.monotonic()
        if last is not None:
            remaining = delay - (now - last)
            if remaining > 0:
                time.sleep(remaining)
        self._last_fetch[key] = time.monotonic()

    def reset(self):
        self._cache.clear()
        self._last_fetch.clear()
        self._override.clear()


# Module-level singleton: one robots cache for the whole run.
_GATE = RobotsGate()


def can_fetch(url):
    return _GATE.can_fetch(url)


def crawl_delay(url):
    return _GATE.crawl_delay(url)


def status(url):
    return _GATE.status(url)


def add_override(url):
    _GATE.add_override(url)


def add_scoped_override(url, path_pattern):
    _GATE.add_override(url, path_pattern=path_pattern)


def is_override(url):
    return _GATE.is_override(url)


def wait(url):
    _GATE.wait(url)


def get(url, **kwargs):
    return _GATE.get(url, **kwargs)


def reset():
    _GATE.reset()
