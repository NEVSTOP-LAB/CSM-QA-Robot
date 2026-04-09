# Token 优化策略调研

## 1. Token 消耗来源分析

| 来源 | 占比（估算） | 优化空间 |
|------|-------------|---------|
| System Prompt（固定指令） | 10–20% | Prompt Caching（-50%） |
| RAG 注入的 Wiki 片段 | 40–60% | 精准检索（减少 k）、片段压缩 |
| 用户评论原文 | 5–10% | 截断超长评论 |
| 输出（回复正文） | 20–30% | 限制 max_tokens |

## 2. Prompt Caching（最高优先级）

**原理：** LLM 服务端缓存 Prompt 前缀的 KV 计算结果，相同前缀的重复请求直接复用，节省输入 token 计费。

| 提供商 | 机制 | 节省 |
|--------|------|------|
| OpenAI | 自动（前缀 ≥1024 tokens，128 token 粒度） | 缓存 token 按 **50%** 计费 |
| Anthropic Claude | 显式 `cache_control` 标注 | 缓存读取按 **10%** 计费 |

**实施要点：**
- 将**固定内容**（角色设定、回复规则）置于 System Prompt 最前
- RAG 检索出的 Wiki 片段紧跟其后（同一文章的多条评论批量处理时，同一 Wiki 片段会命中缓存）
- **动态内容**（评论原文）放在 User 消息，永不破坏前缀缓存

```
[System - 静态前缀，触发缓存]
  角色设定（100 tokens）
  回复规则（200 tokens）
  Wiki 片段（500 tokens）← 同一批次相同

[User - 每次不同]
  评论原文（50~200 tokens）
```

参考：[OpenAI Prompt Caching](https://openai.com/index/api-prompt-caching/) | [Anthropic Caching Guide](https://www.morphllm.com/prompt-caching)

## 3. RAG 精准检索（减少注入量）

### 3.1 控制 Top-K

```python
# 默认 k=3，约 900–1500 tokens；对简单问题 k=2 即够
results = vectorstore.similarity_search(query, k=2)
```

### 3.2 相似度阈值过滤

```python
results = vectorstore.similarity_search_with_score(query, k=5)
# 只保留相似度 > 0.75 的片段
filtered = [doc for doc, score in results if score > 0.75]
```

无相关片段时，不注入 Wiki，仅用通用回复模板（大幅降低 token）。

### 3.3 片段压缩（Contextual Compression）

用轻量模型对检索到的 Wiki 片段提取关键句，再注入主 LLM：

```python
from langchain.retrievers.document_compressors import LLMChainExtractor
compressor = LLMChainExtractor.from_llm(cheap_llm)  # 用 gpt-4o-mini 压缩
compressed = compressor.compress_documents(docs, query)
```

> 可将注入 token 减少 30–60%，代价是额外一次小模型调用（费用极低）。

参考：[LangChain Contextual Compression](https://python.langchain.com/docs/how_to/contextual_compression/)

## 4. 批量处理同一文章的评论

同一篇文章的评论在一次 Action run 中**批量处理**，而非逐条调用：

```python
# ❌ 逐条：每次都重新检索 + 重新发送 System Prompt
for comment in new_comments:
    reply = generate_reply(comment, retrieve_context(comment.text))

# ✅ 批量：同一文章一次检索，Wiki 片段复用（命中 Prompt Cache）
wiki_ctx = retrieve_context(article_summary, k=3)  # 基于文章整体检索
for comment in new_comments:
    reply = generate_reply(comment, wiki_ctx)  # 相同 System Prompt → 缓存命中
```

## 5. 选用低成本模型

| 任务 | 推荐模型 | 原因 |
|------|----------|------|
| 日常评论回复 | gpt-4o-mini | 质量足够，费用极低 |
| Wiki 片段压缩 | gpt-4o-mini | 轻量提取不需要大模型 |
| Embedding（在线） | text-embedding-3-small | 最便宜，效果好 |
| Embedding（离线） | BAAI/bge-small-zh-v1.5 | 免费，中文优化 |
| 复杂/重要评论 | gpt-4o | 按需升级 |

## 6. 截断超长评论

```python
MAX_COMMENT_TOKENS = 300
def truncate_comment(text: str) -> str:
    tokens = tokenizer.encode(text)
    if len(tokens) > MAX_COMMENT_TOKENS:
        return tokenizer.decode(tokens[:MAX_COMMENT_TOKENS]) + "..."
    return text
```

用 `tiktoken` 精确计算 token 数，避免截断过早或过晚。

## 7. 限制输出长度

```python
client.chat.completions.create(
    ...,
    max_tokens=250,  # 知乎评论回复 200 字以内足够
)
```

## 8. 综合节省效果估算

| 策略 | 单次调用节省 |
|------|------------|
| Prompt Caching（同批次多评论） | 输入 token -50% |
| RAG k=2 + 阈值过滤 | 注入 token -30% |
| 片段压缩 | 注入 token -40%（压缩后） |
| max_tokens 限制 | 输出 token -20% |
| 使用 gpt-4o-mini | 费用 -85%（vs gpt-4o） |

> 综合优化后，相比"全量 Wiki + gpt-4o"方案，**费用可降低 90%以上**。

## 9. 参考资源

- [Token-Efficient RAG (DZone)](https://dzone.com/articles/token-efficient-rag-using-query-intent-to-reduce-cost)
- [Minimize LLM Token Usage in RAG (apxml.com)](https://apxml.com/courses/optimizing-rag-for-production/chapter-5-cost-optimization-production-rag/minimize-llm-token-usage-rag)
- [Context-Aware RAG - Microsoft](https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/context-aware-rag-system-with-azure-ai-search-to-cut-token-costs-and-boost-accur/4456810)
- [Prompt Caching Comparison (OpenAI vs Anthropic)](https://www.prompthub.us/blog/prompt-caching-with-openai-anthropic-and-google-models)
- [Long Context RAG Performance - Databricks](https://www.databricks.com/blog/long-context-rag-performance-llms)
