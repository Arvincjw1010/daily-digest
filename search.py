"""信息采集模块：RSS feeds + 可选 Web 搜索"""

import re
import time
import feedparser


def _strip_html(text: str) -> str:
    """去掉 HTML 标签，保留纯文本。"""
    if not text:
        return ""
    # 先移除 <script>/<style> 块
    text = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', text, flags=re.DOTALL | re.IGNORECASE)
    # 替换常见块标签为空格
    text = re.sub(r'</?(p|br|div|li|tr|h\d)[^>]*>', ' ', text, flags=re.IGNORECASE)
    # 去掉剩余所有标签
    text = re.sub(r'<[^>]+>', '', text)
    # 合并空白
    text = re.sub(r'\s+', ' ', text).strip()
    # 清理 HN RSS 元数据噪声
    text = re.sub(r'Article URL:\s*\S+\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Comments URL:\s*\S+\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Points:\s*\d+\s*', '', text)
    text = re.sub(r'# Comments:\s*\d+\s*', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def fetch_rss(feed_url: str, max_items: int = 15) -> list[dict]:
    """抓取并解析一个 RSS feed，返回文章列表。"""
    try:
        feed = feedparser.parse(feed_url)
        items = []
        for entry in feed.entries[:max_items]:
            raw = entry.get("summary", entry.get("description", ""))
            items.append(
                {
                    "title": _strip_html(entry.get("title", "")),
                    "url": entry.get("link", ""),
                    "content": _strip_html(raw)[:500],
                    "published": entry.get("published", ""),
                }
            )
        return items
    except Exception as e:
        print(f"  [WARN] RSS 抓取失败: {feed_url} - {e}")
        return []


def fetch_rss_for_interest(interest: dict) -> list[dict]:
    """为一个兴趣领域抓取所有 RSS 源，按 URL 去重合并。
    每个源各自取 max_articles 条，保证多源都被覆盖。"""
    all_items = []
    seen_urls = set()

    per_feed = interest.get("max_articles", 8)

    for feed_url in interest.get("rss_feeds", []):
        items = fetch_rss(feed_url, max_items=per_feed)
        for item in items:
            if item["url"] and item["url"] not in seen_urls:
                seen_urls.add(item["url"])
                all_items.append(item)
        print(f"    {feed_url.split('//')[1].split('/')[0]}: +{len(items)}")

    # 最终截断：交叉来源去重后，取 max_articles * 2（留余地给后续过滤）
    return all_items[: per_feed * 2]


def search_web_for_interest(interest: dict) -> list[dict]:
    """
    可选：通过 DuckDuckGo 搜索今日热点（免费，无需 API key）。
    每个关键词单独搜索，结果合并去重。
    如果 duckduckgo_search 未安装则静默跳过。
    """
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        return []

    keywords = interest.get("keywords", [])
    if not keywords:
        return []

    all_results = []
    seen_urls = set()

    try:
        with DDGS() as ddgs:
            for query in keywords:
                try:
                    for r in ddgs.text(query, max_results=2, region="wt-wt"):
                        url = r.get("href", "")
                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            all_results.append(
                                {
                                    "title": r.get("title", ""),
                                    "url": url,
                                    "content": r.get("body", "")[:500],
                                    "published": "",
                                }
                            )
                except Exception as e:
                    print(f"  [WARN] 搜索 '{query}' 失败: {e}")
                    continue
                time.sleep(0.5)  # 控制频率
    except Exception as e:
        print(f"  [WARN] Web 搜索失败 '{interest['name']}': {e}")

    return all_results


def filter_by_relevance(items: list[dict], interest: dict) -> list[dict]:
    """
    正向匹配 + 负向排除，过滤明显不相关的条目。
    免费且快速，减少后续 LLM API 的浪费。
    """
    pattern = interest.get("title_filter", "")
    exclude = interest.get("exclude_filter", "")
    if not pattern and not exclude:
        return items

    try:
        pos_regex = re.compile(pattern, re.IGNORECASE) if pattern else None
    except re.error as e:
        print(f"  [WARN] title_filter 正则错误: {e}")
        return items

    try:
        neg_regex = re.compile(exclude, re.IGNORECASE) if exclude else None
    except re.error as e:
        print(f"  [WARN] exclude_filter 正则错误: {e}")
        return items

    filtered = []
    for item in items:
        title = item.get("title", "")
        content = item.get("content", "")[:200]
        combined = f"{title} {content}"

        # 负向排除优先
        if neg_regex and neg_regex.search(combined):
            print(f"  [DROP] 排除: {title[:80]}")
            continue

        # 正向匹配
        if pos_regex and not pos_regex.search(combined):
            print(f"  [DROP] 不相关: {title[:80]}")
            continue

        filtered.append(item)

    dropped = len(items) - len(filtered)
    if dropped:
        print(f"  [FILTER] 过滤掉 {dropped} 条，保留 {len(filtered)} 条")
    return filtered


def search_interest(interest: dict) -> list[dict]:
    """
    为一个兴趣领域收集内容：
      1. RSS feeds（主要来源）
      2. Web 搜索（补充，仅当 duckduckgo_search 安装时生效）
      3. 相关性过滤（标题关键词匹配，避免 LLM 浪费时间）
    """
    name = interest["name"]
    print(f"  [RSS] 抓取 '{name}' 的订阅源...")
    items = fetch_rss_for_interest(interest)

    print(f"  [Web] 搜索 '{name}' 的最新内容...")
    web_items = search_web_for_interest(interest)

    # 与 RSS 结果去重
    seen_urls = {item["url"] for item in items if item["url"]}
    for w in web_items:
        if w["url"] and w["url"] not in seen_urls:
            seen_urls.add(w["url"])
            items.append(w)

    print(f"  -> '{name}' 原始采集 {len(items)} 条")

    # 相关性过滤
    items = filter_by_relevance(items, interest)
    print(f"  -> '{name}' 过滤后 {len(items)} 条")
    return items
