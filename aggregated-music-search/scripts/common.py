#!/usr/bin/env python3
"""Shared models, HTTP client, and URL/text helpers for aggregated music search."""

from __future__ import annotations

import http.cookiejar
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_TIMEOUT = 20
DEFAULT_KUWO_BASE = "https://www.kuwo.cn"
DEFAULT_NETEASE_BASE = "https://music.163.com"
DEFAULT_PROVIDER = "all"
STATE_FILENAME = "last_search.json"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[1] / "outputs"
DEFAULT_STATE_FILE = DEFAULT_OUTPUT_DIR / STATE_FILENAME
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
)
PROVIDER_LABELS = {
    "netease": "网易云",
    "kuwo": "酷我",
    "qqmusic": "QQ音乐",
    "kugou": "酷狗",
    "migu": "咪咕",
}


class SkillError(RuntimeError):
    """Raised for expected workflow failures."""


@dataclass(slots=True)
class Track:
    provider: str
    source_code: str
    track_id: str
    title: str
    artist: str
    album: str
    duration_ms: int | None = None
    source_url: str | None = None
    cover_url: str | None = None


@dataclass(slots=True)
class ProviderContext:
    client: "HttpClient"
    artist_hint: str | None
    limit: int
    kuwo_base: str
    netease_base: str
    state_file: Path


class HttpClient:
    def __init__(self, timeout: int) -> None:
        self.timeout = timeout
        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie_jar)
        )

    def request(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        method: str = "GET",
    ) -> tuple[bytes, Any]:
        request = urllib.request.Request(url, headers=headers or {}, method=method)
        try:
            response = self.opener.open(request, timeout=self.timeout)
            with response:
                return response.read(), response
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise SkillError(f"HTTP {exc.code} for {url}: {body[:240]}") from exc
        except urllib.error.URLError as exc:
            raise SkillError(f"Request failed for {url}: {exc.reason}") from exc
        except TimeoutError as exc:
            raise SkillError(f"Request timed out for {url}") from exc
        except OSError as exc:
            msg = str(exc).lower()
            if "timed out" in msg or "timeout" in msg:
                raise SkillError(f"Request timed out for {url}") from exc
            raise

    def get_text(self, url: str, *, headers: dict[str, str] | None = None) -> str:
        raw, _ = self.request(url, headers=headers)
        return raw.decode("utf-8", errors="replace")

    def get_json(self, url: str, *, headers: dict[str, str] | None = None) -> Any:
        text = self.get_text(url, headers=headers)
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise SkillError(f"Expected JSON from {url}, got: {text[:240]}") from exc

    def get_cookie(self, name: str) -> str | None:
        for cookie in self.cookie_jar:
            if cookie.name == name:
                return cookie.value
        return None


def provider_label(provider: str) -> str:
    return PROVIDER_LABELS.get(provider, provider)


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def normalize_compare(text: str) -> str:
    lowered = text.casefold()
    return re.sub(r"[\W_]+", "", lowered)


def base_origin(base_url: str) -> str:
    parsed = urllib.parse.urlparse(base_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    return origin.rstrip("/")


def strip_trailing_slash(value: str) -> str:
    return value.rstrip("/")


def join_url(base: str, suffix: str) -> str:
    return strip_trailing_slash(base) + suffix


def shared_headers(referer_base: str) -> dict[str, str]:
    origin = base_origin(referer_base)
    return {
        "Accept": "application/json, text/plain, */*",
        "Origin": origin,
        "Referer": origin + "/",
        "User-Agent": USER_AGENT,
    }


def bootstrap_kuwo(client: HttpClient, kuwo_base: str) -> str | None:
    seed_url = join_url(kuwo_base, "/search/list?key=bootstrap")
    client.get_text(seed_url, headers=shared_headers(kuwo_base))
    return client.get_cookie("kw_token")


def kuwo_headers(kuwo_base: str, kw_token: str | None) -> dict[str, str]:
    headers = shared_headers(kuwo_base)
    if kw_token:
        headers["csrf"] = kw_token
    return headers
