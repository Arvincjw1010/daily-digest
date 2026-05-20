"""每日资讯摘要：采集 -> AI 整理 -> 推送"""

import os
import sys
from datetime import date

import yaml
from dotenv import load_dotenv

from search import search_interest
from summarize import summarize_interest
from push import push_to_bark, push_to_wechat_test_account


def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def get_env_or_exit(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        print(f"[FATAL] 环境变量 {name} 未设置")
        sys.exit(1)
    return value


def main():
    load_dotenv()  # 从 .env 文件加载环境变量
    config = load_config()

    # 必填环境变量
    deepseek_api_key = get_env_or_exit("DEEPSEEK_API_KEY")
    bark_key = get_env_or_exit("BARK_KEY")

    deepseek_model = config.get("deepseek", {}).get("model", "deepseek-chat")
    bark_server_url = config.get("push", {}).get("bark", {}).get("server_url")

    all_summaries = []

    # ---- 阶段 1：采集 + 整理 ----
    for interest in config["interests"]:
        name = interest["name"]
        print(f"\n{'='*50}")
        print(f"  领域: {name}")
        print(f"{'='*50}")

        # 采集
        results = search_interest(interest)
        if not results:
            print(f"  -> '{name}' 无内容，跳过")
            continue

        # AI 整理
        print(f"  [AI] 正在用 DeepSeek 整理...")
        summary = summarize_interest(name, results, deepseek_api_key, deepseek_model)
        if summary:
            all_summaries.append(f"# {name}\n\n{summary}")

    # ---- 阶段 2：推送 ----
    if not all_summaries:
        print("\n没有内容需要推送，退出。")
        return

    today = date.today().isoformat()
    title = f"每日资讯 · {today}"
    content = "\n\n---\n\n".join(all_summaries)

    # 推送到 Bark（iPhone）
    print(f"\n{'='*50}")
    print(f"  推送摘要到 iPhone...（共 {len(all_summaries)} 个领域）")
    print(f"{'='*50}")
    push_to_bark(bark_key, title, content, bark_server_url)

    # 可选：推送到微信测试号
    push_config = config.get("push", {})
    wechat_config = push_config.get("wechat", {})
    if wechat_config.get("enabled", False):
        print(f"\n{'='*50}")
        print("  推送到微信测试号...")
        print(f"{'='*50}")
        appid = get_env_or_exit(wechat_config.get("appid_env", "WECHAT_APPID"))
        secret = get_env_or_exit(wechat_config.get("secret_env", "WECHAT_SECRET"))
        template_id = get_env_or_exit(
            wechat_config.get("template_id_env", "WECHAT_TEMPLATE_ID")
        )
        extra = wechat_config.get("recipients", [])
        push_to_wechat_test_account(
            appid, secret, template_id, title, content,
            extra_recipients=extra or None,
        )

    print(f"\n{'='*50}")
    print(f"  完成！今日摘要已推送。")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
