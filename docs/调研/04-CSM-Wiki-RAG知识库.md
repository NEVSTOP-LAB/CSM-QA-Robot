# CSM Wiki RAG 知识库调研

## 1. 问题定义

| 需求 | 挑战 |
|------|------|
| 每次回复都能参考最新 CSM Wiki | Wiki 更新后需同步到检索库 |
| 不全量灌入 Prompt | Token 消耗巨大，且超出上下文窗口 |
| 回复质量高 | 检索要精准，避免引入无关内容 |

## 2. RAG 架构总览

```
CSM Wiki (Markdown 文件)
    │ 定期同步（GitHub Actions cron）
    ▼
文档分块（Chunking）
    │
    ▼
Embedding 生成（text-embedding-3-small）
    │
    ▼
向量存储（ChromaDB / FAISS）← 保存在 data/vector_store/
    │
    ▼
查询时：评论 → Embedding → Top-K 相似片段 → 注入 Prompt
```

## 3. 向量库选型

| 库 | 持久化 | 无服务器 | GitHub Actions 友好 | 元数据查询 | 推荐度 |
|----|--------|----------|---------------------|------------|--------|
| **ChromaDB** | 内置（本地文件） | ✅ | ✅ | ✅ | ⭐⭐⭐⭐⭐ |
| **FAISS** | 手动（save/load） | ✅ | ✅ | ❌（需额外处理） | ⭐⭐⭐⭐ |
| Pinecone | 云服务 | ❌（需联网） | 需 API Key | ✅ | ⭐⭐（复杂度高） |

**推荐：ChromaDB**，开箱即用本地持久化，适合 Git 管理小型向量库。

```bash
pip install chromadb sentence-transformers
```

参考：[DocRAG with FAISS/ChromaDB](https://github.com/EMoetez/DocRAG-with-FAISS)

## 4. Embedding 模型选型

| 模型 | 方式 | 成本 | 中文支持 |
|------|------|------|----------|
| `text-embedding-3-small` (OpenAI) | API 调用 | 极低（$0.02/1M tokens） | 良好 |
| `text-embedding-3-large` (OpenAI) | API 调用 | 稍贵 | 更好 |
| `BAAI/bge-small-zh-v1.5` | 本地运行 | 免费 | 专为中文优化 |

> 推荐：优先使用 `BAAI/bge-small-zh-v1.5`（本地，零成本，中文优秀）  
> Wiki 内容多为中文时尤其适合，可通过 `sentence-transformers` 加载。

## 5. 文档分块策略

```python
# 按 Markdown 标题分块，保留语义完整性
# 每块约 300~500 tokens，带标题前缀用于上下文溯源
def chunk_markdown(text: str, source: str) -> list[dict]:
    sections = re.split(r'\n(?=#{1,3} )', text)
    return [{"text": s.strip(), "source": source} for s in sections if s.strip()]
```

- 按 `#` 标题边界分割，比固定字符截断保留更完整的语义单元
- 每块附带来源文件名，便于回复时引用出处

## 6. 增量更新机制

避免每次全量重建向量库（消耗 embedding API 费用）：

```python
# 维护 data/wiki_hash.json：{文件路径: MD5哈希}
def sync_wiki(wiki_dir: str, vectorstore: Chroma):
    old_hashes = load_hashes("data/wiki_hash.json")
    new_hashes = {}
    for md_file in Path(wiki_dir).glob("**/*.md"):
        content = md_file.read_text()
        h = md5(content)
        new_hashes[str(md_file)] = h
        if old_hashes.get(str(md_file)) != h:
            # 删除旧向量，插入新向量
            vectorstore.delete(where={"source": str(md_file)})
            chunks = chunk_markdown(content, str(md_file))
            vectorstore.add_documents(chunks)
    save_hashes(new_hashes, "data/wiki_hash.json")
```

关键点：
- 只对**变更文件**重新 embedding（节省 API 费用）
- 新增/删除文件均处理
- `wiki_hash.json` 和向量库一起 git commit

参考：[How to Update RAG Knowledge Base Without Rebuilding Everything](https://particula.tech/blog/update-rag-knowledge-without-rebuilding)

## 7. 检索与注入

```python
def retrieve_context(query: str, k: int = 3) -> list[str]:
    results = vectorstore.similarity_search(query, k=k)
    return [doc.page_content for doc in results]
```

- `k=3` 约 900–1500 tokens，足够提供上下文又不过载
- 可加 **reranker**（如 `cross-encoder/ms-marco-MiniLM-L-6-v2`）提升精度，但需权衡延迟

## 8. Wiki 更新频率建议

| Wiki 更新频率 | 同步策略 |
|---------------|---------|
| 偶尔更新（月级） | 手动触发 `workflow_dispatch` 重建 |
| 定期更新（周级） | 每周日专用 `sync-wiki` workflow |
| 高频更新 | Wiki 仓库 push 事件触发同步（webhook） |

## 9. 参考资源

- [LangChain RAG Tutorial](https://python.langchain.com/docs/tutorials/rag/)
- [ChromaDB Docs](https://docs.trychroma.com/)
- [BAAI/bge 中文 Embedding 模型](https://huggingface.co/BAAI/bge-small-zh-v1.5)
- [Context-Aware RAG (Microsoft)](https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/context-aware-rag-system-with-azure-ai-search-to-cut-token-costs-and-boost-accur/4456810)
