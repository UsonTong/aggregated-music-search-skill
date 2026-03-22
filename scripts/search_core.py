#!/usr/bin/env python3
"""CLI workflow for aggregated multi-platform music search."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from common import (
    DEFAULT_KUWO_BASE,
    DEFAULT_NETEASE_BASE,
    DEFAULT_PROVIDER,
    DEFAULT_STATE_FILE,
    DEFAULT_TIMEOUT,
    HttpClient,
    ProviderContext,
    SkillError,
    Track,
    provider_label,
    strip_trailing_slash,
)
from providers import SEARCH_HANDLERS, enrich_track_metadata, search_all_providers, search_provider
from state import load_search_state, save_search_state


def format_track_line(
    index: int,
    track: Track,
    *,
    include_id: bool = False,
    include_album: bool = False,
) -> str:
    parts = [f"{index}. {track.title} - {track.artist}", provider_label(track.provider)]
    if include_album and track.album:
        parts.append(track.album)
    line = " | ".join(parts)
    if include_id:
        line += f" | id={track.track_id}"
    return line


def print_candidates(tracks: list[Track], *, include_id: bool = False) -> None:
    for index, track in enumerate(tracks, start=1):
        print(format_track_line(index, track, include_id=include_id))


def print_candidate_block(tracks: list[Track], *, max_items: int, include_id: bool = False) -> None:
    print("找到这些候选：")
    print_candidates(tracks[: min(len(tracks), max_items)], include_id=include_id)
    print("回复序号即可选择。")


def print_search_summary(errors: dict[str, str]) -> None:
    if not errors:
        return
    print("Search warnings:", file=sys.stderr)
    for provider, message in errors.items():
        print(f"- {provider}: {message}", file=sys.stderr)


def select_track(tracks: list[Track], pick_index: int) -> Track:
    if pick_index < 1 or pick_index > len(tracks):
        raise SkillError(f"--pick-index must be between 1 and {len(tracks)}, got {pick_index}")
    return tracks[pick_index - 1]


def run_search_workflow(args: argparse.Namespace) -> int:
    client = HttpClient(timeout=args.timeout)
    state_file = Path(args.state_file).expanduser().resolve()
    context = ProviderContext(
        client=client,
        artist_hint=args.artist,
        limit=args.limit,
        kuwo_base=strip_trailing_slash(args.kuwo_api_base),
        netease_base=strip_trailing_slash(args.netease_api_base),
        state_file=state_file,
    )

    reused_song = None
    if args.select_index is not None and not args.song:
        reused_song, tracks = load_search_state(state_file)
        search_errors = {}
    else:
        if not args.song:
            raise SkillError("--song is required unless you use --select-index with saved search state.")
        if args.provider == "all":
            tracks, search_errors = search_all_providers(context, args.song)
        else:
            tracks = search_provider(args.provider, context, args.song)
            search_errors = {}
        save_search_state(state_file, song=args.song, tracks=tracks)

    effective_pick = args.select_index if args.select_index is not None else args.pick_index

    if args.list_only:
        print_candidate_block(tracks, max_items=max(effective_pick, 10), include_id=args.debug_ids)
        print_search_summary(search_errors)
        return 0

    print_candidate_block(tracks, max_items=max(effective_pick, 10), include_id=args.debug_ids)
    print_search_summary(search_errors)
    if reused_song:
        print(f"使用上一次搜索结果：{reused_song}")
    track = select_track(tracks, effective_pick)
    track = enrich_track_metadata(context, track)
    print(f"已选择：{track.title} - {track.artist} | {provider_label(track.provider)}")
    print("已保存所选曲目信息。")
    duration_seconds = int(track.duration_ms / 1000) if isinstance(track.duration_ms, int) and track.duration_ms > 0 else None
    print(json.dumps({
        "song": reused_song or args.song,
        "selected_index": effective_pick,
        "title": track.title,
        "artist": track.artist,
        "album": track.album,
        "provider": track.provider,
        "track_id": track.track_id,
        "duration_seconds": duration_seconds,
        "source_url": track.source_url,
        "state_file": str(state_file),
    }, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Search a song by name across one or more providers, merge candidate results, "
            "and save the selected track metadata for later reuse."
        )
    )
    parser.add_argument("--song", help="Song title or search query.")
    parser.add_argument("--artist", help="Optional artist hint for ranking results.")
    parser.add_argument(
        "--provider",
        default=DEFAULT_PROVIDER,
        choices=["all", *sorted(SEARCH_HANDLERS)],
        help="Search provider. Use all to aggregate results across providers (default: all).",
    )
    parser.add_argument("--limit", type=int, default=5, help="Maximum search results to fetch per provider.")
    parser.add_argument("--pick-index", type=int, default=1, help="1-based index of the selected aggregated search result.")
    parser.add_argument("--select-index", type=int, help="Reuse the last saved search result list and select by 1-based index.")
    parser.add_argument("--list-only", action="store_true", help="Only print aggregated ranked search results and exit.")
    parser.add_argument("--debug-ids", action="store_true", help="Include provider track ids in displayed candidate results.")
    parser.add_argument("--state-file", default=str(DEFAULT_STATE_FILE), help="Path to save or reuse the last aggregated search state.")
    parser.add_argument("--kuwo-api-base", default=DEFAULT_KUWO_BASE, help="Override Kuwo base URL. Useful for local mock validation.")
    parser.add_argument("--netease-api-base", default=DEFAULT_NETEASE_BASE, help="Override Netease base URL.")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="HTTP timeout in seconds.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return run_search_workflow(args)
    except SkillError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
