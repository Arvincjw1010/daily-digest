# 架构详解

## 数据流

```
UTC 22:00 (北京时间 06:00)
        │
        ▼
┌─────────────────────────────────────────────────┐
│                  GitHub Actions                  │
│  ubuntu-latest / Python 3.12                    │
│  checkout → pip install → python main.py        │
└─────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────┐
│                main.py (主控)                    │
│  读取 config.yaml → 遍历每个 interest → 合并输出  │
└─────────────────────────────────────────────────┘
        │
        ├──────────────────────────────────────────┐
        ▼                                          ▼
┌──────────────┐                          ┌──────────────┐
│  search.py   │                          │ summarize.py │
│  采集+过滤    │                          │  AI 整理      │
└──────────────┘                          └──────────────┘
        │                                          │
        ├─ fetch_rss()          多源并行抓取          │
        ├─ search_web()         DuckDuckGo 补充       │
        ├─ 去重 (URL)                               │
        └─ filter_by_relevance() 正向+负向正则过滤     │
        │                                          │
        ▼                                          ▼
┌─────────────────────────────────────────────────┐
│                  push.py                         │
│         Bark API → iOS 原生推送                   │
└─────────────────────────────────────────────────┘
```

## 模块详解

### search.py — 信息采集与三层过滤

```
RSS 源 → feedparser 解析 → _strip_html() 清洗
         ↘
Web 搜索  → DuckDuckGo → 每关键词独立搜索
         ↙
    去重合并 (URL)
         ↓
filter_by_relevance()
  ├─ exclude_filter 负向排除 (优先)
  └─ title_filter 正向匹配
         ↓
    最终结果 → 送 summarize.py
```

#### 为什么不用 Tavily API（原计划）

原计划使用 Tavily 搜索 API。实际改用 RSS + DuckDuckGo，原因：
- RSS 源稳定可控，内容质量可预期
- DuckDuckGo 免费无需注册
- Tavily 免费额度 1000 次/月，长期不够用
- RSS 源可以手动调优，API 搜索结果是黑盒

#### 为什么 RSS 源要"每个源独立取"

**问题**：最初 `fetch_rss_for_interest()` 对所有源抓取后按 `max_articles` 截断。结果 OpenAI Blog（排第一个、更新频繁）直接吃满 8 条，Anthropic、Simon Willison 一条都轮不到。

**修复**：改为每个源各自取 `max_articles` 条，去重后取 `max_articles * 2` 作为上限。这样所有源的内容都有机会被采集。

#### _strip_html() — HTML 清洗

RSS 内容常有以下噪声：
- `<script>/<style>` 代码块
- HTML 标签残留
- HN RSS 特有元数据：`Article URL: ...`、`Comments URL: ...`、`Points: N`、`# Comments: N`

清洗流程：
1. 移除 `<script>/<style>` 完整块
2. 替换块级标签为空格（`<p>/<br>/<div>/<li>/<tr>/<h1..6>`）
3. 移除剩余所有 `<...>` 标签
4. 清理 HN 元数据噪声（正则：`Article URL:\s*\S+\s*` 等）
5. 合并多余空白

#### filter_by_relevance() — 双正则过滤

**设计原因**：RSS 源再精准，也会夹带无关内容。OpenAI Blog 80% 是政策白皮书和企业案例。成本极低的标题正则过滤可以在送 LLM 之前砍掉大部分噪声。

**执行顺序**：
1. 负向排除优先（`exclude_filter`）——命中则直接丢弃
2. 正向匹配（`title_filter`）——未命中则丢弃

匹配范围：标题 + 内容前 200 字符（有些 RSS 标题隐晦但内容开头有信号）。

### summarize.py — AI 整理

#### 为什么有三个 prompt

不同的内容类型需要不同的"筛选眼光"：

| 类型 | Prompt 侧重点 | 识别关键词 |
|------|-------------|-----------|
| 大模型产品动态 | 只保留产品更新，扔掉政策/学术/评论 | 名称含 "产品" |
| 国内AI动态 | 关注国产模型进展、政策、落地，排除软广 | 名称含 "国内" |
| 新奇AI工具 | 关注趣味性和可试玩性，排除融资/招聘 | 其他（默认） |

#### Prompt 设计原则

1. **明确告诉 LLM 要扔掉什么**（比告诉它"要什么"更重要）
2. **给正向示例**（如 "OpenAI 发布 GPT-5..." 输出格式）
3. **宁可少而精**：指令写明 "不相关的直接跳过，不要硬凑"
4. **指令用中文**：DeepSeek 对中文指令响应更好

#### max_tokens 演进

- 初始：2048（两个分类够用）
- 当前：4096（三个分类，每类可能 8-10 条）

### push.py — 推送

仅支持 Bark（iOS）。选择 Bark 的原因：
- App Store 免费，iPhone 原生推送
- 支持 Markdown 排版
- 支持分组（所有通知归到 "每日资讯" 组）
- 无需注册账号

## 配置体系

### 三层参数

每个 interest 有三组配置参数：

| 参数组 | 说明 | 示例 |
|--------|------|------|
| `rss_feeds` + `keywords` | 信息来源 | RSS URL 列表 + DuckDuckGo 搜索词 |
| `title_filter` + `exclude_filter` | 过滤规则 | 正则表达式，不区分大小写 |
| `max_articles` | 数量控制 | 每个源取 N 条 |

### 配置调优经验

从本次会话的调优过程总结：

1. **RSS 源要精准不要多**——Hacker News 首页、TechCrunch 首页、arxiv 论文都太泛，产出与 AI 无关。换成 AI 专线源 + HN 关键词过滤后质量飞跃。
2. **正向词要具体**——用 `tool|demo|project` 太泛，导致非 AI 的 shell 工具也进来。改成 `ai|llm|gpt|claude|agent|workflow` 后精准。
3. **负向词要持续迭代**——排除列表是逐步完善的：先发现漏了政策/招聘，加上；又发现漏了标题党/宗教/feature request，再加上。是个持续过程。
4. **Anthropic 没有可用 RSS**——试了 4 个 URL 全返回 0，最终用 `hnrss.org` 的 Anthropic/Claude 关键词过滤源替代。

## 设计决策记录

### 为什么是 RSS + DuckDuckGo 而不是 API 搜索

| 方案 | 优点 | 缺点 |
|------|------|------|
| Tavily API | 结构化结果，语义搜索 | 有配额，花钱，不可控 |
| DuckDuckGo | 免费，无配额 | 结果质量不稳定，限频 |
| RSS | 稳定，可控，免费 | 源少，有些站点无 RSS |

最终方案：RSS 为主（质量稳定），DuckDuckGo 为补充（扩大覆盖）。DuckDuckGo 搜索安装了才启用，没装静默跳过——不增加环境依赖。

### 为什么是 DeepSeek 而不是 Claude/GPT

- 用户已有 DeepSeek API Key
- 成本极低（几分钱/天）
- 中文摘要质量足够
- 不做复杂推理，deepseek-chat 完全够用

### 为什么是 Bark 而不是微信/PushPlus

- Bark 免费且无需注册
- iOS 原生推送体验好
- Markdown 排版支持
- 微信推送需要测试号/企业号，维护成本高
- 如果未来需要安卓支持，可以加 PushPlus 作为备选通道

## 未来扩展方向

### 短期（已规划）

- [ ] 投资理财领域（抓取政策公告、行业招聘数据变化等公开信号源）
- [ ] 职业发展方向（分析特定行业的招聘趋势和技术需求变化）

### 长期（可能的方向）

- [ ] 信号异常检测（不只做摘要，做异常数据预警，如"某行业招聘量骤降 30%"）
- [ ] 多平台推送（Telegram、微信测试号备选）
- [ ] 历史摘要存档（本地 HTML 或 GitHub Pages）
- [ ] 个性化 prompt 调参界面
