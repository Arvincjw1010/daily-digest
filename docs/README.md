# Daily Info Digest · 每日资讯摘要

每天早上 6:00（北京时间），自动推送 AI 行业精选资讯到你的 iPhone。

## 你每天会收到什么

一条 Bark 推送，包含三个板块：

| 板块 | 内容 | 来源 |
|------|------|------|
| **大模型产品动态** | ChatGPT/Claude/Gemini 等主流产品的功能更新、模型升级、API 变动 | OpenAI Blog、Simon Willison、HN 精选 |
| **国内AI动态** | 国产大模型进展、AI 应用落地、政策风向 | 机器之心、量子位、少数派 |
| **新奇AI工具与玩法** | 有趣的 AI 项目、创意应用、社区热议 | Show HN、HN 精选 |

## 为什么做这个

信息环境极度嘈杂：社交媒体算法、标题党自媒体、软文广告、重复搬运——普通人难以分辨什么值得看、什么值得信。

这个工具做的事情：

```
原始信息噪音                    你每天读到的
~~~~~~~~~~~~~~~~~               ~~~~~~~~~~~~
████░░░░░░ 假消息 → 过滤掉 →      ██ 主流产品更新（已筛选，只保留产品相关）
██████░░░░ 标题党 → 过滤掉 →      ██ 国内AI值得关注（已去重，排除软文广告）
████████░░ 软文   → 过滤掉 →      ██ 新奇好玩工具（全是实际项目，不是讨论帖）
██████░░░░ 重复   → 去重    →
██████████ 有用   → 保留    →
```

## 核心设计理念：多层过滤，不只是 AI 摘要

很多「AI 摘要」工具的问题在于：**把噪声摘要一遍，还是噪声**。

我们的做法是在送进 LLM 之前做三道免费过滤，确保花 API 钱的都是值得整理的内容：

| 层 | 做什么 | 成本 |
|----|--------|------|
| **RSS 源精选** | 只从 AI 专线/垂直媒体抓，不要泛科技站 | 免费 |
| **标题正则过滤** | 正向关键词匹配 + 负向排除（政策/招聘/软文） | 免费 |
| **HTML 噪声清洗** | 清掉 RSS 元数据垃圾 | 免费 |
| **DeepSeek 摘要** | 定制 prompt，明确要什么不要什么 | ~¥8-15/月 |

## 成本

| 项目 | 费用 |
|------|------|
| DeepSeek API | ~¥8-15/月（每天 ~15K token） |
| Bark App | 免费 |
| GitHub Actions | 免费（每月 2000 分钟） |
| RSS 源 | 免费 |
| **合计** | **¥8-15/月** |

## 目录结构

```
daily-digest/
├── main.py                 # 主入口：编排采集→整理→推送
├── search.py               # 信息采集：RSS + Web搜索 + 过滤
├── summarize.py            # AI整理：DeepSeek prompt + 摘要
├── push.py                 # 推送：Bark (iOS)
├── config.yaml             # 配置：领域、RSS源、关键词、过滤规则
├── requirements.txt        # Python 依赖
├── test_search.py          # 本地测试脚本（只测采集，不消耗 API）
├── .env.example            # 密钥模板
├── .env                    # 密钥（不进 git）
├── .gitignore              # Git 忽略规则
├── CLAUDE.md               # Claude 会话指引（自动更新文档）
├── docs/                   # 项目文档
│   ├── README.md           # 本文件
│   ├── ARCHITECTURE.md     # 架构详解 + 设计决策
│   ├── CONFIG.md           # 配置指南
│   └── CHANGELOG.md        # 变更记录
└── .github/workflows/
    └── daily-digest.yml    # GitHub Actions 定时任务
```

## 快速开始

### 1. 克隆并安装

```bash
git clone https://github.com/Arvincjw1010/daily-digest.git
cd daily-digest
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置密钥

```bash
cp .env.example .env
# 编辑 .env，填入：
#   DEEPSEEK_API_KEY=sk-你的key
#   BARK_KEY=你的BarkKey
```

- DeepSeek API Key：https://platform.deepseek.com/api_keys
- Bark Key：App Store 下载 Bark，打开 App 即可看到

### 3. 本地测试

```bash
# 只看搜索采集结果（不消耗 API）
python test_search.py

# 完整跑一遍（消耗 DeepSeek API + 推送 Bark）
python main.py
```

### 4. 部署到 GitHub Actions

1. 创建 GitHub 仓库并 push
2. Settings → Secrets and variables → Actions → 添加：
   - `DEEPSEEK_API_KEY`
   - `BARK_KEY`
3. Actions → Daily Info Digest → Run workflow（手动触发测试）
4. 定时任务自动在每天 UTC 22:00（北京时间 06:00）运行

## 添加新领域

编辑 `config.yaml`，在 `interests` 列表里加一项：

```yaml
  - name: "你的领域名"
    rss_feeds:
      - https://example.com/rss
      - https://another.com/feed
    keywords:
      - "搜索关键词1"
      - "搜索关键词2"
    title_filter: "关键词1|关键词2|more"    # 标题必须匹配
    exclude_filter: "广告|软文|排除词"       # 标题命中则丢弃
    max_articles: 8
```

然后在 `summarize.py` 的 `_build_prompt()` 里添加对应的 prompt 模板（在名称中检测关键词）。

更多细节见 [CONFIG.md](./CONFIG.md)。
