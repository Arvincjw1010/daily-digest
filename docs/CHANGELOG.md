# 变更记录

## 2026-06-08 — 重大重构（本次会话）

### 背景

用户测试发现旧版存在严重问题：
- **信号源太泛**：Hacker News 首页、TechCrunch、arxiv 论文产出大量非 AI 内容
- **没有过滤**：所有 RSS 内容直接喂给 LLM，政策白皮书和企业案例混在产品动态里
- **单一分类**：AI 大类一锅端，无法区分产品更新和好玩工具
- **没有国内内容**：完全缺少中文 AI 资讯

### 改动概要

#### config.yaml — 从 1 个大杂烩到 3 个精准分类

**删除的 RSS 源**（产出不相关）：
- `news.ycombinator.com/rss` — HN 全站，太泛
- `arxiv.org/rss/cs.AI` — 学术论文，不是产品
- `feeds.feedburner.com/TechCrunch` — 创业融资大杂烩
- `theverge.com/rss/ai-artificial-intelligence` — 偏消费电子
- `bensbites.beehiiv.com/feed` — 反爬或被墙
- `reddit.com/r/ClaudeAI/.rss` — 反爬
- `reddit.com/r/OpenAI/.rss` — 反爬
- `anthropic.com/blog/rss.xml` — 4 种 URL 变体全返回 0 条

**新增方案**：
```yaml
# 分类 1：大模型产品动态
rss_feeds:
  - openai.com/blog/rss.xml              # 唯一官方源
  - hnrss.org/frontpage?q=anthropic+...  # 替代 Anthropic RSS
  - simonwillison.net/atom/entries/      # 产品观察者
title_filter: ...   # 必须命中产品更新词
exclude_filter: ...  # 排除政策/案例/评论/工具

# 分类 2：国内AI动态（全新）
rss_feeds:
  - jiqizhixin.com/rss     # 机器之心
  - qbitai.com/feed         # 量子位
  - sspai.com/feed          # 少数派
title_filter: ...   # 中文 AI 关键词
exclude_filter: ...  # 排除软文/早报/招聘

# 分类 3：新奇AI工具与玩法
rss_feeds:
  - hnrss.org/show?q=ai+OR+llm+...       # Show HN 纯项目
  - hnrss.org/frontpage?q=ai+tool+...     # HN AI 讨论
title_filter: ...   # 必须命中 AI 关键词
exclude_filter: ...  # 排除招聘/标题党
```

#### search.py — 新增三层过滤体系

1. **`_strip_html()`** — HTML + HN 元数据清洗
   - 清理 `<script>/<style>` 块、HTML 标签
   - 清理 HN RSS 特有元数据（`Article URL:`, `Comments URL:`, `Points:`, `# Comments:`）

2. **`filter_by_relevance()`** — 双正则过滤
   - 负向排除优先（`exclude_filter`）
   - 正向匹配（`title_filter`）
   - 搜索范围：标题 + 内容前 200 字符

3. **多源独立抓取** — 修复单源吃满问题
   - 之前：所有源统一取 `max_articles` 条，OpenAI Blog 排第一个就吃满
   - 现在：每个源各自取 `max_articles` 条，去重后取上限

#### summarize.py — 三类专属 prompt

**之前**：一个 prompt 包打天下，对什么都说「整理成摘要」

**现在**：
- 产品动态 prompt：强调「只保留产品更新」「扔掉政策/学术/评论」
- 国内AI prompt：关注「国产大模型」「应用案例」「政策风向」，排除「软文/早报」
- 新奇工具 prompt：强调「让人想立刻去试」，排除「产品公告」

**其他变更**：
- `max_tokens`: 2048 → 4096（适应三分类）

#### requirements.txt

- 新增 `duckduckgo-search>=6.0.0`（之前代码引用了但未声明依赖）

#### 新增文件

- `test_search.py` — 本地测试脚本，只跑搜索不消耗 API
- `docs/README.md` — 项目概述和快速开始
- `docs/ARCHITECTURE.md` — 架构详解和设计决策
- `docs/CONFIG.md` — 配置指南和过滤调优方法
- `docs/CHANGELOG.md` — 本文件

### 测试结果

**第一轮**（旧配置）：
```
大模型产品动态: 10 条（但 8 条不相关）
- Biodefense 政策白皮书 ❌
- democratic governance 蓝图 ❌
- public policy agenda ❌
- GPT-Rosalind 生命科学 ❌
- Travelers/Endava/Wasmer 企业案例 ❌
- 真正相关的只有 1 条：ChatGPT Memory ✅
```

**最终轮**（新配置）：
```
大模型产品动态: 4 条（全相关）
- ChatGPT Memory ✅
- Claude Opus 4.8 ✅
- Gemini 3.5 Flash ✅

- 排除 8 条噪声（政策、企业案例、技术实验、行业评论）

国内AI动态: ~8 条（新分类，待用户在 GitHub Actions 测试）
新奇AI工具: 9 条（全部 Show HN 实际项目，3 条招聘排除）
```

### 已知限制

| 问题 | 影响 | 状态 |
|------|------|------|
| Anthropic 没有可用 RSS | Claude 动态只能靠 HN 二手 | 已用 hnrss 关键词过滤替代 |
| Ben's Bites / Reddit RSS 被反爬 | 缺失两个来源 | 已移除，等备选方案 |
| Claude 沙箱环境无法本地网络测试 | 开发调试不便 | 靠 test_search.py + GitHub Actions 验证 |
| 仅 iOS Bark 推送 | Android 用户收不到 | 计划后续加 PushPlus 备选 |
| 本地 pip install 受限 | duckduckgo-search 本地装不了 | Actions 环境不受影响 |

### 下一步

- [ ] 用户 push 代码并手动触发 GitHub Actions 测试全链路
- [ ] 根据实际推送效果微调排除规则
- [ ] 评估 DeepSeek 摘要质量，必要时调整 prompt
- [ ] 规划投资/职业发展领域的信号采集
- [ ] 考虑多平台推送支持
