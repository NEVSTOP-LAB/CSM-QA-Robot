# AI-014 实施记录：Cookie+CSRF 评论发布接入

## 状态：✅ 完成（已集成到 ZhihuClient + run_bot）

## 实施内容

### ZhihuClient.post_comment()
- 目标 URL: `https://api.zhihu.com/v4/comments`
- CSRF: 从 Cookie 提取 `_xsrf` → `x-xsrftoken` 请求头
- JSON payload: `{object_id, object_type, content, parent_id}`
- 失败返回 False（不抛异常）
- 无 _xsrf 时直接返回 False

### BotRunner._process_single_comment()
- `manual_mode=True` 时写 pending/（默认 MVP 模式）
- `ZHIHU_AUTO_POST=true` 时调用 post_comment 自动发布
- 发布失败回退到 pending/

## 测试覆盖
- `test_zhihu_client.py::TestPostComment` — 7 tests
  - 成功发布、CSRF 头、参数、parent_id、401、无 xsrf、网络错误

## 验收标准
- [x] POST 请求附加 x-xsrftoken CSRF 头
- [x] 发布失败返回 False
- [x] 支持 manual_mode 和 auto_post 两种模式
