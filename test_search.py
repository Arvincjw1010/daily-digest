"""测试脚本：只跑搜索模块，不调用 API，看采集到什么内容。
用法：从终端运行
    cd daily-digest
    source venv/bin/activate
    pip install duckduckgo-search  # 可选，装了能测 web 搜索
    python test_search.py
"""
import sys
import yaml
from search import search_interest


def main():
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    total = 0
    for interest in config["interests"]:
        name = interest["name"]
        print(f"\n{'='*65}")
        print(f"  {name}")
        print(f"{'='*65}")

        results = search_interest(interest)

        if not results:
            print(f"  ⚠️  0 条结果 — 检查 RSS 源是否可达")
            continue

        for i, r in enumerate(results, 1):
            print(f"\n  [{i}] {r['title']}")
            print(f"      {r['url']}")
            content = ' '.join(r['content'].split())[:150]
            print(f"      {content}...")

        total += len(results)

    print(f"\n{'='*65}")
    print(f"  总计 {total} 条，接下来会交给 DeepSeek 整理")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    main()
