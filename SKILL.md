---
name: aggregated-music-search
description: Search across multiple music providers, merge candidate songs into one result list, and allow index-based selection. Output includes a per-track source_url link for downstream download tools. Use when the user gives a song name and wants pure aggregated music search across platforms (no download/export/send).
---

# Aggregated Music Search

## Single Command (black-box)

Use this search step first:

```bash
python3 scripts/aggregated_music_search.py \
  --song "稻香" \
  --list-only
```

## Installation / Integration Guidance

For any agent integrating this skill, use the minimal flow below and avoid exploring the repository first unless needed:

1. Use the primary entrypoint `scripts/aggregated_music_search.py`.
2. Verify the command surface with:

```bash
python3 scripts/aggregated_music_search.py --help
```

3. Verify the basic behavior with:

```bash
python3 scripts/aggregated_music_search.py --song "稻香" --list-only
```

4. Run the repository smoke test only when a broader self-check is needed:

```bash
bash scripts/smoke_test.sh
```

Integration notes:

- Primary entrypoint: `scripts/aggregated_music_search.py`
- Compatibility entrypoint: `scripts/aggregated_music_search_compat.py`
- Default state file: `outputs/last_search.json`
- Recommended flow: search candidates first, then select by index
- Output contract: see `SKILL.md`

Use repo-local paths directly. The primary entrypoint is `scripts/aggregated_music_search.py`.

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
- Search by song name first, merge results, and return/save results.
- Selected result output includes `source_url`, so downstream download can use link input directly.
- Let the user choose the intended result by index when needed.
- This skill does **not** download, export, or send media.

## Output Contract (must follow exactly)

When returning candidate list, always use:

```text
找到这些候选：
1. 歌名 - 艺人 | 平台
2. 歌名 - 艺人 | 平台
...
回复序号即可选择。
```

Rules:

- Keep one candidate per line.
- Candidate line format must be exactly: `序号. 歌名 - 艺人 | 平台`.
- Do not add extra commentary before/after this block.
- Do not append debug notes/warnings unless the user explicitly asks.

When returning a selected track, always use this fixed card format:

```text
歌名
• 艺人：<值或未知>
• 专辑：<值或未知>
• 时长：<值或未知>
• 链接：<source_url>

搜索结果来自：<平台中文名>（aggregated-music-search）
```

Additional constraints:

- Missing fields must be written as `未知` only.
- Do not write phrases like `（聚合结果未提供）`.
- Keep `搜索结果来自` line exactly as shown, only replacing platform name.

## State File Contract

- Default state file: `outputs/last_search.json`
- Purpose: carry search candidates and selected index metadata.
- Each track stores `source_url`; selected-result JSON also prints `source_url` for URL-based downstream download.
- `--pick-index N`: run a fresh search, then select index `N` from that fresh result set.
- `--select-index N`: skip fresh search and select index `N` from the previously saved result set.

## Internal Resources

- `scripts/aggregated_music_search.py`: primary CLI wrapper for aggregated search.
- `scripts/search_core.py`: CLI workflow and result rendering.
- `scripts/common.py`: shared models, HTTP client, and helper utilities.
- `scripts/providers.py`: provider-specific parse/search logic and ranking.
- `scripts/state.py`: search-state persistence helpers.
- `scripts/aggregated_music_search_compat.py`: compatibility wrapper for older entry names (search-only).

