#!/usr/bin/env python3
"""CLI wrapper for aggregated music search."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

CORE_SCRIPT = Path(__file__).resolve().parent / 'search_core.py'


def load_core_module():
    spec = importlib.util.spec_from_file_location('music_core', CORE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'Failed to load music core from {CORE_SCRIPT}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    return load_core_module().main()


if __name__ == '__main__':
    raise SystemExit(main())
