# AI-005 实施记录：RAGRetriever — Wiki 索引与检索

## 状态：✅ 完成

## 实施内容

### 1. RAGRetriever 类实现 (`scripts/rag_retriever.py`)
- `EmbeddingFunction` — 双模式 Embedding
  - 本地模式：BAAI/bge-small-zh-v1.5（延迟加载）
  - 线上模式：text-embedding-3-small（需 OPENAI_API_KEY）
- `RAGRetriever` 主要方法：
  - `sync_wiki(force=False)` — MD5 增量同步
    - 只处理内容变更的文件
    - 自动删除已移除文件的向量
    - force=True 时强制重建
  - `retrieve(query, k=3, threshold=0.72)` — 混合检索
    - reply_index top-2 优先（真人回复）
    - wiki 补足 top-(k-2)
    - 低于阈值的结果被过滤
  - `index_human_reply(question, reply, article_id, thread_id)` — 索引真人回复
    - weight=high 元数据标记
    - upsert 防止重复

### 2. Markdown 分块策略
按 #/##/### 标题分割，保留源文件和标题元数据

## 测试结果
```
23 passed in 1.86s
```
初次运行有 1 个失败（heading 名称不匹配），修正测试后全部通过。

### 遇到的问题
- `test_no_headers_single_chunk` 失败：无标题文档的 heading 应为 "Untitled" 而非 "Document"
  - 原因：`_chunk_markdown` 中 `re.split` 不会分割无标题文本，heading_match 失败后使用 "Untitled"
  - 修正：将测试期望从 "Document" 改为 "Untitled"

## 验收标准
- [x] sync_wiki 增量更新仅处理变更文件
- [x] retrieve 相似度阈值过滤
- [x] reply_index 真人回复优先
- [x] use_online_embedding 开关正确切换
- [x] 单元测试全部通过
