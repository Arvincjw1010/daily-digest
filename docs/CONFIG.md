# 配置指南

## 快速参考

```yaml
interests:
  - name: "分类名称"         # 用于 prompt 匹配和输出标题
    note: "备注说明"         # 可选，仅文档用途
    rss_feeds:               # RSS 订阅源列表
      - https://example.com/rss
    keywords:                # DuckDuckGo 搜索关键词（每词独立搜索）
      - "搜索短语 1"
      - "搜索短语 2"
    title_filter: "关键词1|关键词2|..."    # 标题正向匹配（正则，大小写不敏感）
    exclude_filter: "排除1|排除2|..."      # 标题负向排除（正则，大小写不敏感）
    max_articles: 8          # 每个 RSS 源取几条
```

## 当前三大分类配置说明

### 1. 大模型产品动态

**目标**：只抓主流大模型的产品更新（功能发布、模型升级、API 变更、定价调整）

**RSS 源**：
| 源 | 为什么选它 |
|----|-----------|
| `openai.com/blog/rss.xml` | ChatGPT/GPT 唯一官方公告渠道 |
| `hnrss.org/frontpage?q=anthropic+OR+claude...` | Anthropic 没有提供可用 RSS，用 HN 社区讨论替代 |
| `simonwillison.net/atom/entries/` | LLM 领域公认最敏锐的产品观察者 |

**正向过滤** (`title_filter`)：
```
chatgpt|claude|gpt-5|gpt-4|anthropic|gemini|llm|
new feature|release|推出|新功能|发布|上线|升级|更新|
memory|codex|agent|api|opus|pro|flash
```

**负向排除** (`exclude_filter`)：
```
policy|governance|safety|blueprint|agenda|youth|
biodefense|rosalind|travelers|endava|wasmer|
democratic|regulation|datasette|opinion|onlyfans|
economy|encyclical|sandbox|micropython|wasm|
product.market fit|profitable quarter|rumor|
please ship|ship.*official|linux desktop|feature request|
lathe|show hn
```

**为什么排除这些**：
- `policy|governance|blueprint...` — OpenAI Blog 有大量政策白皮书，与产品无关
- `rosalind|travelers|endava|wasmer` — 企业案例研究，OpenAI 常见的软文内容
- `datasette` — Simon Willison 经常发自己写的非 AI 工具
- `opinion|product.market fit|profitable quarter` — 行业分析猜测，不是事实性产品更新
- `sandbox|micropython|wasm` — Simon 的技术实验，不是 AI 产品
- `please ship|feature request|linux desktop` — HN 上的请求帖，不是产品事实

### 2. 国内AI动态

**目标**：跟踪中国 AI 行业（国产大模型、应用落地、政策风向、芯片/算力）

**RSS 源**：
| 源 | 为什么选它 |
|----|-----------|
| `jiqizhixin.com/rss` | 国内最权威的 AI 垂直技术媒体 |
| `qbitai.com/feed` | 大模型/自动驾驶/机器人，更新最快 |
| `sspai.com/feed` | 效率工具视角，有 AI 应用体验评测 |

**正向过滤** (`title_filter`)：
```
大模型|AI|人工智能|chatgpt|claude|gpt|llm|deepseek|
文心|通义|豆包|kimi|智谱|百川|开源|发布|推出|上线|
新功能|融资|上市|应用|产品|国产|芯片|算力|agent|智能体
```

**负向排除** (`exclude_filter`)：
```
广告|推广|软文|招聘|实习|校招|社招|活动报名|直播预告|
早报|晚报|日报|周报|福利|抽奖
```

**为什么排除这些**：
- `早报|晚报|日报|周报` — 汇总类内容，没有增量信息
- `广告|推广|软文` — 付费推广内容
- `活动报名|直播预告` — 预告不是新闻
- `招聘|实习|校招|社招` — 招聘信息

### 3. 新奇AI工具与玩法

**目标**：发现让人想立刻去试的有趣 AI 项目和应用

**RSS 源**：
| 源 | 为什么选它 |
|----|-----------|
| `hnrss.org/show?q=ai+OR+llm+OR+gpt+OR+claude...` | Show HN = 纯项目展示，不是讨论帖 |
| `hnrss.org/frontpage?q=ai+tool+OR+llm+app...` | HN 上的 AI 相关热门讨论 |

**正向过滤** (`title_filter`)：
```
ai|llm|gpt|claude|chatgpt|openai|anthropic|gemini|
agent|workflow|copilot|开源|玩法|实验|hack|deck|built with
```

> ⚠️ 注意：`tool|demo|project` 曾经在正向列表里，后来移除。因为太宽泛导致非 AI 项目（如纯 shell 自动补全工具、视频配音工具）混入。

**负向排除** (`exclude_filter`)：
```
hiring|is hiring|YC.*is hiring|job|career|funding|
raise \$|series [a-c]|investor|onlyfans|economy of|
encyclical|please ship|ship.*official|feature request|
pope|religion|catholic
```

## 添加新领域的步骤

### 1. 编辑 config.yaml

```yaml
  - name: "你的领域名"        # 这个名字会被 prompt 匹配使用
    rss_feeds:
      - https://source1.com/rss
      - https://source2.com/feed
    keywords:
      - "搜索词1"
      - "搜索词2"
    title_filter: "核心词1|核心词2|..."      # 不区分大小写
    exclude_filter: "排除1|排除2|..."         # 不区分大小写
    max_articles: 8
```

### 2. 编辑 summarize.py (如果名称不能自动匹配)

在 `_build_prompt()` 函数里加判断条件：

```python
elif "你的领域名" in interest_name:
    angle = """你的专属 prompt 模板..."""
```

当前匹配逻辑：
- 名称含 "产品" → 产品动态 prompt
- 名称含 "国内" → 国内AI prompt
- 其他 → 新奇工具 prompt（默认）

### 3. 本地测试

```bash
python test_search.py
```

观察：
- 哪些源返回了内容（+N 行）
- 过滤掉了什么（[DROP] 行）
- 最终保留的内容是否相关

### 4. 迭代调整

根据测试结果微调：
- 如果太多噪声 → 收窄 `title_filter`，扩展 `exclude_filter`
- 如果内容太少 → 放宽 `title_filter`
- 如果某源一直返回 0 → 换源

## 过滤调优经验

### RSS 源优先级

1. 官方博客 RSS（最权威，但内容可能太泛）
2. 垂直媒体 RSS（质量稳定，覆盖广）
3. HN 关键词过滤源（社区精选，但要加排除规则）
4. DuckDuckGo 搜索（最后手段，质量不可控）

### 过滤规则迭代模式

```
第1轮: 配好基础关键词
第2轮: 跑一次 test_search.py，标注所有不相关条目
第3轮: 把不相关的特征加到 exclude_filter
第4轮: 再跑一次，确认过滤效果
第5轮: 如果发现好内容也被误杀，微调 exclude_filter

重复 2-5 直到满意
```

### 常见问题

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| 某源返回 0 条 | 网络问题 / 源不支持 RSS / 反爬 | 换源，或用 DuckDuckGo 搜索替代 |
| 过滤后全是噪声 | title_filter 太宽 | 收紧正向词，加入更多排除词 |
| 过滤后不到 3 条 | title_filter 太严或排除词太宽 | 放宽正向词，检查误杀 |
| HN 内容质量差 | HN RSS 包含元数据噪声 | 确认 _strip_html() 在清理 |

## 正则语法提示

- `|` = "或"
- `.*` = 任意字符
- `\s` = 空格
- `\\$` = 美元符号（需转义）
- 不区分大小写（代码中已处理）
- 搜索范围：标题 + 内容前 200 字符
