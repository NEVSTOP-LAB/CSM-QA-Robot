# Zhihu-CSM-Reply-Robot

> 知乎 CSM（客户成功管理）专栏自动回复机器人 —— 基于 RAG + DeepSeek LLM，运行于 GitHub Actions

---

## 功能概览

- 📥 定时拉取知乎文章/问题下的新评论
- 🔍 RAG 检索 CSM Wiki 知识库，生成专业回复
- 🤖 调用 DeepSeek（或其他 OpenAI 兼容模型）生成回复内容
- 📝 支持人工审核模式（回复写入 `pending/`，人工确认后发布）
- ⚡ 支持自动发布模式（`ZHIHU_AUTO_POST=true`）
- 🚨 异常自动告警：Cookie 失效、429 限流、预算超限 → 创建 GitHub Issue
- 💰 每日 LLM 费用追踪与预算限制
- 📊 追问上下文管理（多轮对话线程）

---

## 快速开始

### 1. Fork 或克隆仓库

```bash
git clone https://github.com/NEVSTOP-LAB/Zhihu-CSM-Reply-Robot.git
cd Zhihu-CSM-Reply-Robot
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置监控文章

编辑 `config/articles.yaml`，添加需要监控的知乎文章或问题：

```yaml
articles:
  - id: "98765432"
    title: "CSM 最佳实践系列（一）"
    url: "https://zhuanlan.zhihu.com/p/98765432"
    type: "article"       # article（专栏文章）或 question（知乎问题）
  - id: "123456789"
    title: "如何做好客户成功？"
    url: "https://www.zhihu.com/question/123456789"
    type: "question"
```

### 4. 准备 CSM Wiki 知识库

将 Markdown 格式的 CSM 知识文档放入 `csm-wiki/` 目录：

```
csm-wiki/
├── 01-客户成功概述.md
├── 02-NPS与CSAT指标.md
├── 03-客户健康度模型.md
└── ...
```

### 5. 配置 GitHub Secrets

在仓库 **Settings → Secrets and variables → Actions** 中添加以下 Secrets：

| Secret 名称 | 必填 | 说明 |
|---|---|---|
| `ZHIHU_COOKIE` | ✅ | 知乎完整 Cookie 字符串（含 `z_c0` 和 `_xsrf`） |
| `LLM_API_KEY` | ✅ | DeepSeek 或 OpenAI API Key |
| `LLM_BASE_URL` | ❌ | API 端点，默认 `https://api.deepseek.com` |
| `LLM_MODEL` | ❌ | 模型名称，默认 `deepseek-chat` |
| `ZHIHU_AUTO_POST` | ❌ | 设为 `true` 启用自动发布，否则写入 `pending/` 待审核 |

#### 获取知乎 Cookie

1. 浏览器登录知乎
2. 打开开发者工具 → Network → 任意知乎请求
3. 复制请求头中完整的 `Cookie` 字段值

### 6. 调整运行参数（可选）

编辑 `config/settings.yaml`：

```yaml
bot:
  check_interval_hours: 6          # 检查间隔（与 cron 表达式对应）
  max_new_comments_per_run: 20     # 每次最多处理条数
  max_new_comments_per_day: 100    # 每日上限
  llm_budget_usd_per_day: 0.50    # 每日 LLM 费用预算（超出后停止并告警）

review:
  manual_mode: true                # true=人工审核模式；false=自动发布

filter:
  spam_keywords:                   # 广告关键词（命中则跳过）
    - "加微信"
    - "私信"
```

---

## 运行方式

### GitHub Actions（推荐）

仓库内置两个 Workflow：

| Workflow | 触发方式 | 功能 |
|---|---|---|
| `bot.yml` | 每6小时 + 手动触发 | 拉取评论 → 生成回复 → 写入 pending/ |
| `sync-wiki.yml` | 每周日 + 手动触发 | 增量同步 CSM Wiki 向量库 |

**手动触发**：仓库页面 → **Actions** → 选择 Workflow → **Run workflow**

### 本地运行

```bash
# 设置环境变量
export ZHIHU_COOKIE="z_c0=xxx; _xsrf=yyy; ..."
export LLM_API_KEY="sk-xxx"
export LLM_BASE_URL="https://api.deepseek.com"   # 可选
export LLM_MODEL="deepseek-chat"                  # 可选

# 运行机器人
python scripts/run_bot.py

# 手动同步 Wiki（强制重建向量库）
python scripts/wiki_sync.py
FORCE_REBUILD=true python scripts/wiki_sync.py
```

---

## 目录结构

```
Zhihu-CSM-Reply-Robot/
├── .github/workflows/
│   ├── bot.yml              # 主 Workflow（定时回复）
│   └── sync-wiki.yml        # Wiki 同步 Workflow
├── config/
│   ├── settings.yaml        # 全局运行参数
│   └── articles.yaml        # 监控文章列表
├── csm-wiki/                # CSM 知识库 Markdown 文档（自行添加）
├── data/
│   ├── seen_ids.json        # 已处理评论 ID 记录
│   ├── vector_store/        # ChromaDB 向量库（自动生成）
│   └── reply_index/         # 历史回复向量索引
├── pending/                 # 待审核回复（人工审核模式）
├── archive/                 # 已发布/归档回复
├── scripts/
│   ├── run_bot.py           # 主入口
│   ├── wiki_sync.py         # Wiki 同步 CLI
│   ├── zhihu_client.py      # 知乎 API 封装
│   ├── rag_retriever.py     # RAG 检索模块
│   ├── llm_client.py        # LLM 调用模块
│   ├── thread_manager.py    # 多轮对话管理
│   ├── comment_filter.py    # 评论前置过滤
│   ├── alerting.py          # GitHub Issue 告警
│   ├── cost_tracker.py      # 费用追踪
│   └── archiver.py          # 归档管理
└── tests/                   # 单元测试（174 个）
```

---

## 人工审核流程

当 `review.manual_mode: true`（默认）时，机器人不直接发布回复，而是写入 `pending/` 目录：

```
pending/
└── 2024-04-10_comment_12345678.md   ← 待审核回复
```

每个文件包含 YAML front-matter 和回复正文：

```markdown
---
article_id: "98765432"
comment_id: "12345678"
commenter: "知乎用户"
status: pending
generated_at: "2024-04-10T10:00:00"
---

您好！关于 CSM 的核心概念...
```

**审核并发布**：将文件中 `status: pending` 改为 `status: approved`，下次 Workflow 运行时自动发布。

---

## 告警机制

以下异常会自动在 GitHub 仓库创建 Issue（标签 `bot-alert`）：

| 告警类型 | 触发条件 |
|---|---|
| Cookie 失效 | HTTP 401 / 403 |
| 持续限流 | HTTP 429 重试耗尽 |
| 连续失败 | 连续失败 ≥ 3 次（可配置） |
| 预算超限 | 当日 LLM 费用 > 预算上限 |

---

## 开发与测试

```bash
# 运行全部测试
python -m pytest tests/ -v

# 运行特定模块测试
python -m pytest tests/test_zhihu_client.py -v
python -m pytest tests/test_llm_client.py -v
```

