#!/usr/bin/env python3
"""Compatibility wrapper for older entry names; runs search only."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SEARCH_SCRIPT = SKILL_DIR / 'scripts' / 'aggregated_music_search.py'


def main() -> int:
    parser = argparse.ArgumentParser(description='Run aggregated multi-platform search only (compat mode).')
    parser.add_argument('query_or_index', nargs='?')
    parser.add_argument('--song')
    parser.add_argument('--provider', default='all', choices=['all', 'netease', 'qqmusic', 'kugou', 'kuwo', 'migu'])
    parser.add_argument('--artist')
    parser.add_argument('--state-file')
    parser.add_argument('--pick-index', type=int, default=1)
    parser.add_argument('--select-index', type=int)
    parser.add_argument('--limit', type=int)
    parser.add_argument('--debug-ids', action='store_true')
    parser.add_argument('--list-only', action='store_true')
    args = parser.parse_args()

    song = args.song or (None if (args.query_or_index or '').isdigit() else args.query_or_index)
    select_index = args.select_index or (int(args.query_or_index) if (args.query_or_index or '').isdigit() else None)

    cmd = [sys.executable, str(SEARCH_SCRIPT), '--provider', args.provider, '--pick-index', str(args.pick_index)]
    if song:
        cmd += ['--song', song]
    if select_index is not None:
        cmd += ['--select-index', str(select_index)]
    if args.artist:
        cmd += ['--artist', args.artist]
    if args.state_file:
        cmd += ['--state-file', args.state_file]
    if args.limit is not None:
        cmd += ['--limit', str(args.limit)]
    if args.debug_ids:
        cmd += ['--debug-ids']
    if args.list_only:
        cmd += ['--list-only']
    return subprocess.run(cmd).returncode


if __name__ == '__main__':
    raise SystemExit(main())
