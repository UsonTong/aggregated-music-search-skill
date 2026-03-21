---
name: aggregated-music-search
description: Search across multiple music providers, merge candidate songs into one result list, allow index-based selection, and persist search state for handoff to the download skill. Use when the user gives a song name and wants pure aggregated music search across platforms (no download/export/send).
---

# Aggregated Music Search

## Single Command (black-box)

Use this search step first:

```bash
python3 skills/aggregated-music-search/scripts/aggregated_music_search.py \
  --song "稻香" \
  --list-only
```

The default saved state file is:

```text
skills/aggregated-music-search/outputs/last_search.json
```

Optional args:

- `--provider all` (default; aggregate search across providers)
- `--provider netease`
- `--provider qqmusic`
- `--provider kugou`
- `--provider kuwo`
- `--provider migu`
- `--artist "周杰伦"`
- `--pick-index 2`
- `--select-index 2` (reuse the saved result list)
- `--debug-ids`
- `--state-file /custom/path/last_search.json`

## Behavior

- Treat this skill as a pure multi-platform search + selection workflow.
- Default provider is `all`, which searches across multiple providers first.
- Search by song name first, merge results, and save state for later reuse by `music-download`.
- Let the user choose the intended result by index when needed.
- This skill does **not** download, export, or send media.

## State File Contract

- Default state file: `skills/aggregated-music-search/outputs/last_search.json`
- Purpose: carry search candidates and selected index metadata into the download step.
- `--pick-index N`: run a fresh search, then select index `N` from that fresh result set.
- `--select-index N`: skip fresh search and select index `N` from the previously saved result set.

## Internal Resources

- `scripts/aggregated_music_search.py`: primary CLI wrapper for aggregated search.
- `scripts/search_core.py`: CLI workflow and result rendering.
- `scripts/common.py`: shared models, HTTP client, and helper utilities.
- `scripts/providers.py`: provider-specific parse/search logic and ranking.
- `scripts/state.py`: search-state persistence helpers.
- `scripts/aggregated_music_search_compat.py`: compatibility wrapper for older entry names (search-only).

