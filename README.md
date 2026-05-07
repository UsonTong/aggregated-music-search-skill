# aggregated-music-search-skill

一个用于**多平台聚合搜索歌曲**的 skill。

## 功能说明

- 按歌曲名搜索（可选歌手提示）
- 聚合多个平台候选结果
- 对结果进行排序并返回可选列表
- 持久化搜索状态

## 安装 / 接入指引

给任意 agent 接入本 skill 时，优先按下面流程执行，不需要先通读仓库：

1. 主入口使用 `scripts/aggregated_music_search.py`。
2. 仅先运行：

```bash
python3 scripts/aggregated_music_search.py --help
```

3. 再做最小功能验证：

```bash
python3 scripts/aggregated_music_search.py --song "稻香" --list-only
```

4. 只有在需要仓库级自检时，再运行：

```bash
bash scripts/smoke_test.sh
```

接入约定：

- 主入口：`scripts/aggregated_music_search.py`
- 兼容入口：`scripts/aggregated_music_search_compat.py`
- 默认状态文件：`outputs/last_search.json`
- 推荐流程：先搜索候选列表，再按序号选择
- 输出契约：见 `SKILL.md`

## 常用命令

```bash
python3 scripts/aggregated_music_search.py --song "稻香" --list-only
```

```bash
python3 scripts/aggregated_music_search.py --song "稻香" --pick-index 2
```

```bash
python3 scripts/aggregated_music_search.py --select-index 2
```

更多接入与输出约定见 `SKILL.md`。
