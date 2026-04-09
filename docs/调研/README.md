# 调研总览

本目录汇总了构建"知乎 CSM 自动回复机器人"所需的各技术方向调研报告。

## 整体架构

```
GitHub Actions (定时触发)
    │
    ▼
知乎数据抓取 (API v4 / Cookie)
    │  新评论检测（与本地存档比对）
    ▼
有新评论？
    │ Yes
    ▼
RAG 检索 CSM Wiki（向量检索）
    │
    ▼
LLM 生成回复 (GPT-like API)
    │
    ▼
知乎 API 发布回复
    │
    ▼
Markdown 归档存储 → Git commit → 推送
```

## 调研文档列表

| 文档 | 内容 |
|------|------|
| [01-知乎数据获取.md](./01-知乎数据获取.md) | 知乎 API/CLI、认证方案、反爬对策 |
| [02-GitHub-Actions自动化.md](./02-GitHub-Actions自动化.md) | 定时触发、Secrets 管理、状态持久化 |
| [03-LLM接入与回复生成.md](./03-LLM接入与回复生成.md) | OpenAI 兼容 API、Prompt 设计 |
| [04-CSM-Wiki-RAG知识库.md](./04-CSM-Wiki-RAG知识库.md) | RAG 架构、向量库选型、增量更新 |
| [05-回复归档与存储.md](./05-回复归档与存储.md) | Markdown 存档结构、Git 追踪 |
| [06-Token优化策略.md](./06-Token优化策略.md) | Prompt 缓存、RAG 压缩、分层检索 |
