"""信息采集模块：RSS feeds + 可选 Web 搜索"""

import time
import feedparser


def fetch_rss(feed_url: str, max_items: int = 15) -> list[dict]:
    """抓取并解析一个 RSS feed，返回文章列表。"""
    try:
        feed = feedparser.parse(feed_url)
        items = []
        for entry in feed.entries[:max_items]:
            items.append(
                {
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "content": entry.get("summary", entry.get("description", ""))[
                        :500
                    ],
                    "published": entry.get("published", ""),
                }
            )
        return items
    except Exception as e:
        print(f"  [WARN] RSS 抓取失败: {feed_url} - {e}")
        return []


def fetch_rss_for_interest(interest: dict) -> list[dict]:
    """为一个兴趣领域抓取所有 RSS 源，按 URL 去重合并。"""
    all_items = []
    seen_urls = set()

    for feed_url in interest.get("rss_feeds", []):
        items = fetch_rss(feed_url)
        for item in items:
            if item["url"] and item["url"] not in seen_urls:
                seen_urls.add(item["url"])
                all_items.append(item)

    max_articles = interest.get("max_articles", 5)
    return all_items[:max_articles]


def search_web_for_interest(interest: dict) -> list[dict]:
    """
    可选：通过 DuckDuckGo 搜索今日热点（免费，无需 API key）。
    如果 duckduckgo_search 未安装则静默跳过。
    """
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        return []

    keywords = interest.get("keywords", [])
    if not keywords:
        return []

    query = " ".join(keywords)
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=3, region="wt-wt"):
                results.append(
                    {
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "content": r.get("body", "")[:500],
                        "published": "",
                    }
                )
        time.sleep(1)  # 控制频率，避免被限
    except Exception as e:
        print(f"  [WARN] Web 搜索失败 '{interest['name']}': {e}")

    return results


def search_interest(interest: dict) -> list[dict]:
    """
    为一个兴趣领域收集内容：
      1. RSS feeds（主要来源）
      2. Web 搜索（补充，仅当 duckduckgo_search 安装时生效）
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

    print(f"  -> '{name}' 共收集 {len(items)} 条内容")
    return items
