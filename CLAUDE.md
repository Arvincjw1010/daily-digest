# CLAUDE.md — Daily Digest 项目指引

## 项目概述

daily-digest 是一个每日 AI 资讯自动推送系统：GitHub Actions 定时抓取 RSS + 搜索 → DeepSeek 整理摘要 → Bark 推送到 iPhone。

**设计目标**：用多层免费过滤（源精选 + 正则过滤 + Prompt 约束）在信息噪声中提取高信号内容。

**核心架构**：
```
GitHub Actions (UTC 22:00 / 北京时间 06:00)
 → main.py 编排
   → search.py (RSS + DuckDuckGo + 双正则过滤)
   → summarize.py (DeepSeek API + 三类定制 Prompt)
   → push.py (Bark iOS 推送)
```

## 三个信息分类

| 分类 | 名称匹配 | RSS 源 | 过滤特点 |
|------|---------|--------|---------|
| 大模型产品动态 | 名称含"产品" | OpenAI + hnrss Anthropic + Simon Willison | 严：排除政策/案例/评论/工具 |
| 国内AI动态 | 名称含"国内" | 机器之心 + 量子位 + 少数派 | 中：排除软文/早报/招聘 |
| 新奇AI工具 | 其他（默认） | Show HN + HN AI filtered | 宽：排除招聘/标题党 |

## 文件职责

| 文件 | 职责 | 修改时注意 |
|------|------|-----------|
| `config.yaml` | 所有配置：RSS 源、过滤词、prompt 角度 | 改完跑 `python test_search.py` 验证 |
| `search.py` | 采集+过滤，零 API 成本 | `_strip_html()` 处理 HTML 噪声，`filter_by_relevance()` 双向正则 |
| `summarize.py` | DeepSeek prompt 模板 | `_build_prompt()` 按名称匹配分发，新分类要加分支 |
| `push.py` | Bark iOS 推送 | 无特殊逻辑 |
| `main.py` | 主控流程 | 不改 |
| `test_search.py` | 本地测试，只看采集不消耗 API | 调试新 RSS 源必用 |
| `.github/workflows/daily-digest.yml` | 定时触发 | 改 cron 注意 UTC 换算 |

## 重要约定

### 过滤规则迭代方法

每次修改 `title_filter` 或 `exclude_filter` 后：
1. 在用户终端跑 `python test_search.py`（不要在 Claude 沙箱跑，网络会被拦截）
2. 用户贴回输出
3. 标注不相关的条目 → 加到 `exclude_filter`
4. 标注误杀的条目 → 从 `exclude_filter` 移除或调整

### 新领域的添加步骤

1. 在 `config.yaml` 加一个 interest
2. 在 `summarize.py` 的 `_build_prompt()` 加对应 prompt
3. 跑 `test_search.py` 验证采集质量
4. 更新 `docs/` 下相关文档

### 网络限制

- Claude 沙箱只能访问 `api.deepseek.com`、`api.anthropic.com` 等有限域名
- 所有 RSS 抓取、git push 都需要用户在终端执行
- GitHub Actions 环境无网络限制，不影响定时任务

### 敏感信息

- `.env` 文件包含真实 API Key，**绝对不能提交**
- 已在 `.gitignore` 中排除

### 推送目标

- 当前仅 Bark (iOS)
- 用户有计划扩展到更多平台

## 文档体系

每次重大修改后，**必须同步更新以下文档**：

| 文档 | 内容 | 更新时机 |
|------|------|---------|
| `docs/README.md` | 项目概述、快速开始 | 架构变化时 |
| `docs/ARCHITECTURE.md` | 架构详解、设计决策 | 模块逻辑变更时 |
| `docs/CONFIG.md` | 配置指南、调优方法 | 配置格式或过滤规则变化时 |
| `docs/CHANGELOG.md` | 按日期记录的变更历史 | **每次修改后必须追加** |

## 用户偏好

- 关注 AI 产品动态（ChatGPT、Claude 等的功能更新）和国内 AI 动态
- 喜欢新奇好玩的 AI 工具
- 未来想扩展到投资理财、职业发展、吃喝玩乐领域
- 核心痛点：信息不对称、无法分辨真假和重要性
- 工具理念：多层级过滤减少噪声，宁可少而精

## 当前待办

- [ ] 用户在 GitHub Actions 手动触发测全链路
- [ ] 根据首次推送质量微调排除规则
- [ ] 规划投资/职业发展领域的信息采集方案
