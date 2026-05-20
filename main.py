"""每日资讯摘要：采集 → AI 整理 → 推送 Bark"""

import os
import sys
from datetime import date

import yaml
from dotenv import load_dotenv

from search import search_interest
from summarize import summarize_interest
from push import push_to_bark


def load_config() -> dict:
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)


def main():
    load_dotenv()

    deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
    bark_key = os.environ.get("BARK_KEY")
    if not deepseek_key or not bark_key:
        print("[FATAL] 请设置 DEEPSEEK_API_KEY 和 BARK_KEY")
        sys.exit(1)

    config = load_config()
    model = config.get("deepseek", {}).get("model", "deepseek-chat")

    all_sections = []

    for interest in config["interests"]:
        name = interest["name"]
        print(f"\n{'='*50}")
        print(f"  领域: {name}")
        print(f"{'='*50}")

        results = search_interest(interest)
        if not results:
            print(f"  无内容，跳过")
            continue

        print(f"  DeepSeek 整理中...")
        summary = summarize_interest(name, results, deepseek_key, model)
        if summary:
            all_sections.append(f"# {name}\n\n{summary}")

    if not all_sections:
        print("\n没有内容，退出。")
        return

    today = date.today().isoformat()
    title = f"每日资讯 · {today}"
    body = "\n\n---\n\n".join(all_sections)

    print(f"\n{'='*50}")
    print(f"  推送到 iPhone...")
    print(f"{'='*50}")
    push_to_bark(bark_key, title, body)

    print(f"\n{'='*50}")
    print(f"  完成！")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
