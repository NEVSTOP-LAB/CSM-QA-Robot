# AI-013 实施记录：真人回复高权重索引

## 状态：✅ 完成（已集成到 RAGRetriever + run_bot）

## 实施内容

### RAGRetriever.index_human_reply()
- 组合 QA 对作为索引文本：`"问题：{question}\n回复：{reply}"`
- weight=high 元数据标记
- upsert 防止重复

### BotRunner._handle_human_reply()
- 检测 `is_author_reply=True` 的评论
- 追加到线程文件（⭐ 标记）
- 索引到 reply_index

### RAGRetriever.retrieve() 优先级
- 先从 reply_index 取 top-2 真人回复
- 再从 wiki 补足

## 测试覆盖
- `test_rag_retriever.py::TestIndexHumanReply` — 4 tests
- `test_run_bot.py::TestProcessArticle::test_human_reply_indexed` — 1 test

## 验收标准
- [x] is_author_reply 时调用 index_human_reply
- [x] reply_index 中存储 weight=high
- [x] retrieve 时 reply_index 优先
