# LLM 接入与回复生成调研

## 1. API 兼容性

本项目使用 **OpenAI 兼容接口**（Chat Completions），支持接入：
- OpenAI（GPT-4o, GPT-4o-mini 等）
- Azure OpenAI
- 任意兼容 `/v1/chat/completions` 的自托管或第三方模型

通过环境变量 `OPENAI_BASE_URL` 切换 endpoint，无需改代码。

```python
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
)
```

参考：[openai-python SDK](https://github.com/openai/openai-python)

## 2. 回复生成流程

```
用户评论 → [RAG 检索相关 CSM 片段] → 组装 Prompt → LLM → 生成回复文本
```

### Prompt 结构（三段式）

```
System（静态，适合 Prompt Caching）:
  你是 CSM 助理，代表专栏作者回复知乎评论。
  回复风格：专业、友善、简洁（200 字内）。
  [CSM Wiki 相关片段] ← RAG 动态注入，放在 System 尾部

User（每次不同）:
  文章标题：{title}
  原评论：{comment_text}
  历史回复摘要（可选）：{summary}
```

> 将 System Prompt 的**固定部分**放在最前，RAG 片段紧随其后；动态内容（评论原文）放 User，最大化缓存命中率。

## 3. 模型选型建议

| 模型 | 优势 | 适用场景 |
|------|------|----------|
| GPT-4o-mini | 低成本、快速 | 日常批量回复 |
| GPT-4o | 质量更高 | 复杂技术问题 |
| 本地模型（Ollama/vLLM） | 零 token 费用 | 私有化部署 |

推荐默认使用 **gpt-4o-mini** 控制成本，对重要评论可升级。

## 4. 调用示例

```python
def generate_reply(comment: str, context_chunks: list[str], article_title: str) -> str:
    wiki_context = "\n\n".join(context_chunks)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "你是 CSM 助理，代表专栏作者回复知乎评论。"
                    "回复风格：专业、友善、简洁（200字内）。\n\n"
                    f"参考知识库：\n{wiki_context}"
                ),
            },
            {
                "role": "user",
                "content": f"文章：{article_title}\n评论：{comment}",
            },
        ],
        temperature=0.7,
        max_tokens=300,
    )
    return response.choices[0].message.content
```

## 5. 回复质量控制

- **温度**：0.5–0.8，平衡一致性与自然度
- **max_tokens**：300 以内（知乎评论不宜过长）
- **后处理**：去除 Markdown 格式（知乎支持有限），过滤敏感词
- **人工审核模式**（可选）：生成后写入待审文件，人工确认后再发布

## 6. 错误处理

```python
import time
from openai import RateLimitError, APIError

def call_with_retry(fn, max_retries=3):
    for i in range(max_retries):
        try:
            return fn()
        except RateLimitError:
            time.sleep(2 ** i)
        except APIError as e:
            if e.status_code >= 500:
                time.sleep(2 ** i)
            else:
                raise
    raise RuntimeError("LLM call failed after retries")
```

## 7. 参考资源

- [OpenAI Python SDK 文档](https://github.com/openai/openai-python)
- [OpenAI API Reference - Chat Completions](https://platform.openai.com/docs/api-reference/chat)
- [Prompt Caching - OpenAI](https://openai.com/index/api-prompt-caching/)
