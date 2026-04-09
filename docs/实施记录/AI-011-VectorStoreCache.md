# AI-011 实施记录：向量库外部化 — Actions Cache 方案

## 状态：✅ 完成（已在 bot.yml 和 sync-wiki.yml 中配置）

## 实施内容

### Actions Cache 配置（`.github/workflows/bot.yml`）
已在 Workflow 中通过 `actions/cache@v4` 实现向量库持久化：

```yaml
- name: Cache vector stores
  uses: actions/cache@v4
  with:
    path: |
      data/vector_store
      data/reply_index
    key: vectors-${{ runner.os }}-${{ github.run_number }}
    restore-keys: |
      vectors-${{ runner.os }}-
```

### 缓存策略
- **key**: 使用 `github.run_number` 确保每次运行生成新缓存
- **restore-keys**: 回退匹配最近的缓存
- **路径**: `data/vector_store/`（Wiki 索引）+ `data/reply_index/`（真人回复索引）

### HuggingFace 模型缓存
同样使用 Actions Cache 缓存 `~/.cache/huggingface`：
```yaml
- name: Cache HuggingFace models
  uses: actions/cache@v4
  with:
    path: ~/.cache/huggingface
    key: hf-${{ runner.os }}-bge-small-zh-v1.5
```

## 验收标准
- [x] 向量库通过 Actions Cache 持久化
- [x] 每次运行可恢复上次的向量库
- [x] HuggingFace 模型缓存避免重复下载
