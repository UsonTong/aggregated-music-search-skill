#!/usr/bin/env python3
"""Provider-specific parsing and search for aggregated music search."""

from __future__ import annotations

import difflib
import json
import urllib.parse
from typing import Any, Callable

from common import (
    USER_AGENT,
    ProviderContext,
    SkillError,
    Track,
    bootstrap_kuwo,
    join_url,
    kuwo_headers,
    normalize_compare,
    normalize_space,
    shared_headers,
)


def parse_kuwo_track(item: dict[str, Any], kuwo_base: str) -> Track | None:
    rid = item.get("rid") or item.get("id") or item.get("DC_TARGETID")
    musicrid = item.get("musicrid") or item.get("MUSICRID") or item.get("MP3RID")
    if not rid and isinstance(musicrid, str) and "_" in musicrid:
        rid = musicrid.split("_", 1)[1]
    if not rid:
        return None

    rid_text = str(rid)
    title = normalize_space(str(item.get("name") or item.get("songName") or item.get("NAME") or ""))
    artist = normalize_space(str(item.get("artist") or item.get("artistName") or item.get("ARTIST") or ""))
    album = normalize_space(str(item.get("album") or item.get("albumName") or item.get("ALBUM") or ""))
    duration_value = item.get("duration") or item.get("DURATION")
    duration_ms = None
    if isinstance(duration_value, str) and duration_value.isdigit():
        duration_value = int(duration_value)
    if isinstance(duration_value, int):
        duration_ms = duration_value if duration_value > 1000 else duration_value * 1000

    return Track(
        provider="kuwo",
        source_code="kw",
        track_id=rid_text,
        title=title or rid_text,
        artist=artist or "Unknown Artist",
        album=album or "",
        duration_ms=duration_ms,
        source_url=join_url(kuwo_base, f"/play_detail/{rid_text}"),
    )


def parse_netease_track(item: dict[str, Any], netease_base: str) -> Track | None:
    track_id = item.get("id")
    if track_id is None:
        return None

    artists = item.get("artists") if isinstance(item.get("artists"), list) else item.get("ar")
    artist_names: list[str] = []
    if isinstance(artists, list):
        for artist in artists:
            if isinstance(artist, dict):
                name = artist.get("name")
                if isinstance(name, str) and name.strip():
                    artist_names.append(normalize_space(name))
    if not artist_names:
        artist_field = item.get("artist") or item.get("singer")
        if isinstance(artist_field, str) and artist_field.strip():
            artist_names = [normalize_space(artist_field)]

    album_data = item.get("album") if isinstance(item.get("album"), dict) else item.get("al")
    album_name = ""
    cover_url = None
    if isinstance(album_data, dict):
        album_name = normalize_space(str(album_data.get("name") or ""))
        cover = album_data.get("picUrl") or album_data.get("pic")
        if isinstance(cover, str) and cover.startswith(("http://", "https://")):
            cover_url = cover

    return Track(
        provider="netease",
        source_code="wy",
        track_id=str(track_id),
        title=normalize_space(str(item.get("name") or "")) or str(track_id),
        artist=" / ".join(artist_names) or "Unknown Artist",
        album=album_name,
        duration_ms=item.get("duration") or item.get("dt"),
        source_url=join_url(netease_base, f"/song?id={track_id}"),
        cover_url=cover_url,
    )


def parse_qqmusic_track(item: dict[str, Any]) -> Track | None:
    mid = item.get("mid") or item.get("songmid")
    if not mid:
        return None
    title = normalize_space(str(item.get("title") or item.get("songname") or ""))
    singers = item.get("singer") if isinstance(item.get("singer"), list) else None
    singer_names: list[str] = []
    if singers:
        for singer in singers:
            if isinstance(singer, dict):
                name = singer.get("name")
                if isinstance(name, str) and name.strip():
                    singer_names.append(normalize_space(name))
    if not singer_names:
        fallback = item.get("artist") or item.get("singername")
        if isinstance(fallback, str) and fallback.strip():
            singer_names.append(normalize_space(fallback))

    album_data = item.get("album") if isinstance(item.get("album"), dict) else None
    album_name = normalize_space(str((album_data or {}).get("name") or item.get("albumname") or ""))

    return Track(
        provider="qqmusic",
        source_code="tx",
        track_id=str(mid),
        title=title or str(mid),
        artist=" / ".join(singer_names) or "Unknown Artist",
        album=album_name,
        source_url=f"https://y.qq.com/n/ryqq/songDetail/{mid}",
    )


def parse_kugou_track(item: dict[str, Any]) -> Track | None:
    file_hash = item.get("FileHash") or item.get("hash") or item.get("EMixSongID")
    if not file_hash:
        return None
    title = normalize_space(str(item.get("SongName") or item.get("songname") or item.get("songName") or ""))
    artist = normalize_space(str(item.get("SingerName") or item.get("singername") or item.get("singer") or ""))
    album = normalize_space(str(item.get("AlbumName") or item.get("album_name") or ""))
    duration = item.get("Duration") or item.get("duration")
    duration_ms = None
    if isinstance(duration, str) and duration.isdigit():
        duration = int(duration)
    if isinstance(duration, int):
        duration_ms = duration * 1000 if duration < 1000 else duration
    return Track(
        provider="kugou",
        source_code="kg",
        track_id=str(file_hash),
        title=title or str(file_hash),
        artist=artist or "Unknown Artist",
        album=album,
        duration_ms=duration_ms,
        source_url=f"https://www.kugou.com/song/#hash={file_hash}",
    )


def parse_migu_track(item: dict[str, Any]) -> Track | None:
    song_id = item.get("copyrightId") or item.get("id") or item.get("songId")
    if not song_id:
        return None
    singers = item.get("singers")
    singer_names: list[str] = []
    if isinstance(singers, list):
        for singer in singers:
            if isinstance(singer, dict):
                name = singer.get("name")
                if isinstance(name, str) and name.strip():
                    singer_names.append(normalize_space(name))
    singer_fallback = item.get("singer")
    if not singer_names and isinstance(singer_fallback, str) and singer_fallback.strip():
        singer_names = [normalize_space(singer_fallback)]

    return Track(
        provider="migu",
        source_code="mg",
        track_id=str(song_id),
        title=normalize_space(str(item.get("songName") or item.get("name") or "")) or str(song_id),
        artist=" / ".join(singer_names) or "Unknown Artist",
        album=normalize_space(str(item.get("album") or item.get("albumName") or "")),
        source_url=f"https://music.migu.cn/v3/music/song/{song_id}",
    )


def score_track(query: str, track: Track, artist_hint: str | None) -> float:
    query_norm = normalize_compare(query)
    title_norm = normalize_compare(track.title)
    artist_norm = normalize_compare(track.artist)
    album_norm = normalize_compare(track.album)

    # 1) Strong relevance first (title/artist/original-like signals)
    score = 0.0
    title_ratio = difflib.SequenceMatcher(a=query_norm, b=title_norm).ratio() if query_norm else 0.0

    if query_norm and title_norm == query_norm:
        score += 180
    elif query_norm and query_norm in title_norm:
        score += 95
    score += title_ratio * 65

    if artist_hint:
        hint_norm = normalize_compare(artist_hint)
        if hint_norm and artist_norm == hint_norm:
            score += 120
        elif hint_norm and hint_norm in artist_norm:
            score += 70
        score += difflib.SequenceMatcher(a=hint_norm, b=artist_norm).ratio() * 30

    if title_norm and artist_norm:
        score += difflib.SequenceMatcher(a=query_norm, b=f"{title_norm}{artist_norm}").ratio() * 10

    if album_norm and query_norm and query_norm in album_norm:
        score += 8

    # Prefer original/studio-like versions; softly demote remix/live/demo/accompaniment-like variants.
    variant_penalty_keywords = (
        "伴奏", "demo", "live", "dj", "remix", "翻唱", "童声", "纯音乐",
        "女声版", "男声版", "合唱", "cover", "翻自", "改编", "版本"
    )
    lower_title = track.title.casefold()
    if any(k in lower_title for k in variant_penalty_keywords):
        score -= 18

    # 2) Provider preference only as secondary tie-break.
    provider_boost = {
        "qqmusic": 10,
        "netease": 10,
        "kuwo": 2,
        "kugou": 2,
        "migu": 1,
    }
    score += provider_boost.get(track.provider, 0)

    return score


def search_qqmusic(context: ProviderContext, query: str) -> list[Track]:
    query_string = urllib.parse.urlencode({"w": query, "n": context.limit, "format": "json"})
    url = f"https://c.y.qq.com/soso/fcgi-bin/client_search_cp?{query_string}"
    payload = context.client.get_json(url, headers={"User-Agent": USER_AGENT, "Referer": "https://y.qq.com/"})
    data = payload.get("data") if isinstance(payload, dict) else None
    song = data.get("song") if isinstance(data, dict) else None
    items = song.get("list") if isinstance(song, dict) else None
    if not isinstance(items, list):
        raise SkillError(f"Unexpected QQMusic search response shape: {payload!r}")
    tracks = [track for item in items if isinstance(item, dict) and (track := parse_qqmusic_track(item))]
    if not tracks:
        raise SkillError(f"No QQMusic search results for {query!r}")
    tracks.sort(key=lambda track: score_track(query, track, context.artist_hint), reverse=True)
    return tracks


def search_kugou(context: ProviderContext, query: str) -> list[Track]:
    query_string = urllib.parse.urlencode({"keyword": query, "pagesize": context.limit, "page": 1})
    url = f"https://songsearch.kugou.com/song_search_v2?{query_string}"
    payload = context.client.get_json(url, headers={"User-Agent": USER_AGENT})
    data = payload.get("data") if isinstance(payload, dict) else None
    items = data.get("lists") if isinstance(data, dict) else None
    if not isinstance(items, list):
        raise SkillError(f"Unexpected Kugou search response shape: {payload!r}")
    tracks = [track for item in items if isinstance(item, dict) and (track := parse_kugou_track(item))]
    if not tracks:
        raise SkillError(f"No Kugou search results for {query!r}")
    tracks.sort(key=lambda track: score_track(query, track, context.artist_hint), reverse=True)
    return tracks


def search_kuwo(context: ProviderContext, query: str) -> list[Track]:
    query_string = urllib.parse.urlencode({"key": query, "pn": 1, "rn": context.limit, "httpsStatus": 1})
    api_url = join_url(context.kuwo_base, f"/api/www/search/searchMusicBykeyWord?{query_string}")

    last_error: SkillError | None = None
    for attempt in range(2):
        kw_token = context.client.get_cookie("kw_token") or bootstrap_kuwo(context.client, context.kuwo_base)
        headers = kuwo_headers(context.kuwo_base, kw_token)
        try:
            payload = context.client.get_json(api_url, headers=headers)
            data = payload.get("data") if isinstance(payload, dict) else None
            items = data.get("list") if isinstance(data, dict) else None
            if not isinstance(items, list):
                raise SkillError(f"Unexpected Kuwo search response shape: {payload!r}")
            tracks = [track for item in items if isinstance(item, dict) and (track := parse_kuwo_track(item, context.kuwo_base))]
            if not tracks:
                raise SkillError(f"No Kuwo search results for {query!r}")
            tracks.sort(key=lambda track: score_track(query, track, context.artist_hint), reverse=True)
            return tracks
        except SkillError as exc:
            last_error = exc
            if attempt == 1:
                break
    raise SkillError(f"Kuwo search failed after retry: {last_error}")


def search_netease(context: ProviderContext, query: str) -> list[Track]:
    headers = {
        **shared_headers(context.netease_base),
        "Accept": "application/json, text/plain, */*",
        "Origin": context.netease_base,
        "Referer": join_url(context.netease_base, "/"),
        "User-Agent": USER_AGENT,
    }
    query_string = urllib.parse.urlencode({"s": query, "limit": context.limit, "type": 1, "offset": 0})
    api_url = join_url(context.netease_base, f"/api/search/get?{query_string}")
    payload = context.client.get_json(api_url, headers=headers)
    result = payload.get("result") if isinstance(payload, dict) else None
    items = result.get("songs") if isinstance(result, dict) else None
    if not isinstance(items, list):
        raise SkillError(f"Unexpected Netease search response shape: {payload!r}")
    tracks = [track for item in items if isinstance(item, dict) and (track := parse_netease_track(item, context.netease_base))]
    if not tracks:
        raise SkillError(f"No Netease search results for {query!r}")
    tracks.sort(key=lambda track: score_track(query, track, context.artist_hint), reverse=True)
    return tracks


def search_migu(context: ProviderContext, query: str) -> list[Track]:
    query_string = urllib.parse.urlencode({
        "text": query,
        "pageNo": 1,
        "pageSize": context.limit,
        "searchSwitch": json.dumps({"song": 1}, separators=(",", ":")),
    })
    url = f"https://pd.musicapp.migu.cn/MIGUM3.0/v1.0/content/search_all.do?{query_string}"
    payload = context.client.get_json(url, headers={"User-Agent": USER_AGENT})
    data = payload.get("songResultData") if isinstance(payload, dict) else None
    items = data.get("result") if isinstance(data, dict) else None
    if not isinstance(items, list):
        raise SkillError(f"Unexpected Migu search response shape: {payload!r}")
    tracks = [track for item in items if isinstance(item, dict) and (track := parse_migu_track(item))]
    if not tracks:
        raise SkillError(f"No Migu search results for {query!r}")
    tracks.sort(key=lambda track: score_track(query, track, context.artist_hint), reverse=True)
    return tracks


SEARCH_HANDLERS: dict[str, Callable[[ProviderContext, str], list[Track]]] = {
    "kuwo": search_kuwo,
    "netease": search_netease,
    "qqmusic": search_qqmusic,
    "kugou": search_kugou,
    "migu": search_migu,
}


def search_provider(provider: str, context: ProviderContext, query: str) -> list[Track]:
    handler = SEARCH_HANDLERS.get(provider)
    if not handler:
        raise SkillError(f"Unsupported provider: {provider}")
    return handler(context, query)


def enrich_track_metadata(context: ProviderContext, track: Track) -> Track:
    """Best-effort metadata enrichment after selection (duration)."""
    try:
        if track.provider == "netease":
            headers = {
                **shared_headers(context.netease_base),
                "Accept": "application/json, text/plain, */*",
                "Origin": context.netease_base,
                "Referer": join_url(context.netease_base, "/"),
                "User-Agent": USER_AGENT,
            }
            query_string = urllib.parse.urlencode({"ids": f"[{track.track_id}]"})
            api_url = join_url(context.netease_base, f"/api/song/detail/?{query_string}")
            payload = context.client.get_json(api_url, headers=headers)
            songs = payload.get("songs") if isinstance(payload, dict) else None
            if isinstance(songs, list) and songs and isinstance(songs[0], dict):
                detail = songs[0]
                duration_ms = detail.get("dt") or detail.get("duration")
                if isinstance(duration_ms, int) and duration_ms > 0 and not track.duration_ms:
                    track.duration_ms = duration_ms
    except SkillError:
        return track
    except Exception:
        return track
    return track


def dedupe_tracks(query: str, tracks: list[Track], artist_hint: str | None) -> list[Track]:
    best_by_key: dict[str, Track] = {}
    best_score: dict[str, float] = {}
    for track in tracks:
        key = f"{normalize_compare(track.title)}::{normalize_compare(track.artist)}"
        if not key or key == "::":
            key = f"{track.provider}::{track.track_id}"
        score = score_track(query, track, artist_hint)
        if key not in best_by_key or score > best_score[key]:
            best_by_key[key] = track
            best_score[key] = score
    deduped = list(best_by_key.values())
    deduped.sort(key=lambda track: score_track(query, track, artist_hint), reverse=True)
    return deduped


def search_all_providers(context: ProviderContext, query: str) -> tuple[list[Track], dict[str, str]]:
    combined: list[Track] = []
    errors: dict[str, str] = {}
    for provider in SEARCH_HANDLERS:
        try:
            combined.extend(search_provider(provider, context, query))
        except SkillError as exc:
            errors[provider] = str(exc)
    if not combined:
        detail = "; ".join(f"{provider}: {msg}" for provider, msg in errors.items()) or "no providers returned results"
        raise SkillError(f"No search results from any provider for {query!r}. Details: {detail}")
    return dedupe_tracks(query, combined, context.artist_hint), errors

