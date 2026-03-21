#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPTS_DIR="$ROOT_DIR/scripts"

python3 -m py_compile "$SCRIPTS_DIR"/*.py
python3 "$SCRIPTS_DIR/aggregated_music_search.py" --help >/dev/null
python3 "$SCRIPTS_DIR/aggregated_music_search_compat.py" --help >/dev/null

echo "smoke test ok"
