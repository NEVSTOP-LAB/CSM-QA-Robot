# AI-004 实施记录：GitHub Actions Workflow 基础版

## 状态：✅ 完成

## 实施内容

### 1. bot.yml — 主 Workflow
- 触发：`schedule cron '0 2,8,14,20 * * *'`（每6小时）+ `workflow_dispatch`
- 权限：`contents: write` + `issues: write`
- 步骤：checkout → setup-python 3.11 → pip cache → HuggingFace cache → vector store cache → pip install → run_bot.py → git commit+push
- Secrets 引用：ZHIHU_COOKIE, LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, GITHUB_TOKEN, ZHIHU_AUTO_POST
- 提交时使用 `[skip ci]` 防止循环触发
- 先配置 git user.name/email 再 commit

### 2. sync-wiki.yml — Wiki 同步 Workflow
- 触发：每周日 UTC 00:00 + workflow_dispatch（支持 force_rebuild 参数）
- 同样包含 pip/HuggingFace/vector store 缓存

## 测试结果
```
17 passed in 0.12s
```

覆盖：bot.yml 结构验证（15 tests）+ sync-wiki.yml 结构验证（2 tests）

## 验收标准
- [x] Workflow 可手动触发（workflow_dispatch）
- [x] 脚本路径为 scripts/run_bot.py
- [x] HuggingFace 缓存配置存在
- [x] git 提交不因缺少身份配置而失败
- [x] commit message 包含 [skip ci]
