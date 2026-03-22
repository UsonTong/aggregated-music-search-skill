#!/usr/bin/env python3
"""State persistence helpers for aggregated music search."""

from __future__ import annotations

import ast
import json
from dataclasses import asdict
from pathlib import Path

from common import SkillError, Track


def save_search_state(state_file: Path, *, song: str, tracks: list[Track]) -> None:
    state_file.parent.mkdir(parents=True, exist_ok=True)
    payload = {"song": song, "tracks": [asdict(track) for track in tracks]}
    state_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_search_state(state_file: Path) -> tuple[str | None, list[Track]]:
    if not state_file.exists():
        raise SkillError(f"Search state file not found: {state_file}")
    text = state_file.read_text(encoding="utf-8").strip()
    if not text:
        raise SkillError(f"Search state file is empty: {state_file}")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        # Backward-compatibility with historical literal format.
        try:
            payload = ast.literal_eval(text)
        except (ValueError, SyntaxError) as exc:
            raise SkillError(f"Failed to parse search state file: {state_file}") from exc
    if not isinstance(payload, dict):
        raise SkillError(f"Invalid search state payload: {payload!r}")
    song = payload.get("song")
    raw_tracks = payload.get("tracks")
    if not isinstance(raw_tracks, list) or not raw_tracks:
        raise SkillError("Search state has no tracks.")
    tracks: list[Track] = []
    for item in raw_tracks:
        if not isinstance(item, dict):
            continue
        try:
            tracks.append(Track(**item))
        except TypeError:
            continue
    if not tracks:
        raise SkillError("Search state has no valid tracks.")
    return (song if isinstance(song, str) else None), tracks
