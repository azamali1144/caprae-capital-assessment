import asyncio
import logging
import time
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit
from urllib.robotparser import RobotFileParser

import httpx
from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from app.core.cache import cache_get_json, cache_set_json
from app.core.config import get_settings

log = logging.getLogger(__name__)

MAX_BODY_BYTES = 2 * 1024 * 1024
ROBOTS_TTL = 60 * 60 * 24
HOST_DELAY_SECONDS = 0.5


@dataclass
class FetchResult:
    url: str
    status: int | None = None
    html: str | None = None
    final_url: str | None = None
    elapsed_ms: int = 0
    error: str | None = None  # timeout | blocked_robots | not_html | too_large | http_xxx | ...

    @property
    def ok(self) -> bool:
        return self.html is not None and self.error is None

    @property
    def is_https(self) -> bool:
        return (self.final_url or self.url).startswith("https://")


class _Retryable(Exception):
    """Raised for stuff worth another go: timeouts, 5xx, 429."""


def _should_retry(exc: BaseException) -> bool:
    return isinstance(exc, _Retryable | httpx.TimeoutException | httpx.ConnectError)


class Fetcher:
    """Polite async fetcher: robots.txt, retries with backoff, small per-host delay."""

    def __init__(self, client: httpx.AsyncClient | None = None, host_delay: float | None = None):
        s = get_settings()
        self.user_agent = s.crawl_user_agent
        self.client = client or httpx.AsyncClient(
            timeout=httpx.Timeout(s.crawl_timeout_seconds),
            follow_redirects=True,
            http2=True,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.5",
            },
            limits=httpx.Limits(max_connections=50, max_keepalive_connections=20),
        )
        self.host_delay = HOST_DELAY_SECONDS if host_delay is None else host_delay
        self._host_locks: dict[str, asyncio.Lock] = {}
        self._host_last_hit: dict[str, float] = {}
        self._robots: dict[str, RobotFileParser | None] = {}

    async def aclose(self) -> None:
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self.aclose()

    # --- robots.txt -------------------------------------------------------

    async def _load_robots(self, base: str) -> RobotFileParser | None:
        host = urlsplit(base).netloc
        if host in self._robots:
            return self._robots[host]

        key = f"robots:{host}"
        body = await cache_get_json(key)
        if body is None:
            body = ""
            try:
                resp = await self.client.get(urljoin(base, "/robots.txt"))
                # missing robots.txt means everything is allowed
                if resp.status_code == 200:
                    body = resp.text[:100_000]
                elif resp.status_code in (401, 403):
                    body = "User-agent: *\nDisallow: /"
            except httpx.HTTPError:
                body = ""
            await cache_set_json(key, body, ROBOTS_TTL)

        parser = RobotFileParser()
        parser.parse(body.splitlines())
        self._robots[host] = parser
        return parser

    async def allowed(self, url: str) -> bool:
        parts = urlsplit(url)
        parser = await self._load_robots(f"{parts.scheme}://{parts.netloc}")
        return parser is None or parser.can_fetch(self.user_agent, url)

    # --- politeness -------------------------------------------------------

    async def _wait_turn(self, host: str) -> None:
        lock = self._host_locks.setdefault(host, asyncio.Lock())
        async with lock:
            gap = time.monotonic() - self._host_last_hit.get(host, 0)
            if gap < self.host_delay:
                await asyncio.sleep(self.host_delay - gap)
            self._host_last_hit[host] = time.monotonic()

    # --- fetching ---------------------------------------------------------

    async def _get_once(self, url: str) -> httpx.Response:
        await self._wait_turn(urlsplit(url).netloc)
        resp = await self.client.get(url)
        if resp.status_code == 429 or resp.status_code >= 500:
            raise _Retryable(f"http_{resp.status_code}")
        return resp

    async def fetch(self, url: str, check_robots: bool = True) -> FetchResult:
        started = time.perf_counter()
        result = FetchResult(url=url)

        def done() -> FetchResult:
            result.elapsed_ms = int((time.perf_counter() - started) * 1000)
            return result

        if check_robots and not await self.allowed(url):
            result.error = "blocked_robots"
            return done()

        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(2),
                wait=wait_exponential(multiplier=0.5, max=4),
                retry=retry_if_exception(_should_retry),
                reraise=False,
            ):
                with attempt:
                    resp = await self._get_once(url)
        except RetryError as exc:
            last = exc.last_attempt.exception()
            if isinstance(last, httpx.TimeoutException):
                result.error = "timeout"
            elif isinstance(last, httpx.ConnectError):
                result.error = "connect_error"
            else:
                result.error = str(last) or "retry_exhausted"
            return done()
        except httpx.HTTPError as exc:
            log.debug("fetch failed %s: %s", url, exc)
            result.error = type(exc).__name__.lower()
            return done()

        result.status = resp.status_code
        result.final_url = str(resp.url)

        if resp.status_code >= 400:
            result.error = f"http_{resp.status_code}"
            return done()

        ctype = resp.headers.get("content-type", "")
        if "html" not in ctype.lower():
            result.error = "not_html"
            return done()

        if len(resp.content) > MAX_BODY_BYTES:
            result.error = "too_large"
            return done()

        result.html = resp.text
        return done()
