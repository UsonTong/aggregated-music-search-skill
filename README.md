# aggregated-music-search-skill

一个用于**多平台聚合搜索歌曲**的 skill。

## 功能说明

- 按歌曲名搜索（可选歌手提示）
- 聚合多个平台候选结果
- 对结果进行排序并返回可选列表
- 持久化搜索状态

## 常用命令

```bash
python3 aggregated-music-search/scripts/aggregated_music_search.py \
  --song "稻香" \
  --list-only
```

默认状态文件：

- `aggregated-music-search/outputs/last_search.json`
