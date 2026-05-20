"""每日资讯摘要：采集 -> AI 整理 -> 推送"""

import os
import sys
from datetime import date

import yaml
from dotenv import load_dotenv

from search import search_interest
from summarize import summarize_interest
from push import push_to_bark, push_to_wechat_test_account
from html_generator import generate_html


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

    # 必填
    deepseek_api_key = get_env_or_exit("DEEPSEEK_API_KEY")

    deepseek_model = config.get("deepseek", {}).get("model", "deepseek-chat")

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
    full_content = "\n\n---\n\n".join(all_summaries)

    # 生成 HTML 页面（推送到 Vercel）
    digest_url = None
    try:
        html = generate_html(title, all_summaries)
        os.makedirs("public", exist_ok=True)
        with open("public/index.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("  [OK] HTML 页面已生成: public/index.html")
        digest_url = "https://daily-digest.vercel.app/"
    except Exception as e:
        print(f"  [WARN] HTML 生成失败: {e}")

    # 为微信生成简短版（只提取标题行）
    wechat_lines = []
    for summary in all_summaries:
        for line in summary.split("\n"):
            line = line.strip()
            # 提取 DeepSeek 输出中的标题行（以 ** 开头或 - ** 开头的行）
            if line.startswith("**") and line.endswith("**"):
                wechat_lines.append(line.strip("*").strip())
            elif line.startswith("- **"):
                title = line.split("**")[1] if "**" in line else line[:40]
                wechat_lines.append(title)
    wechat_content = "\n".join(wechat_lines[:8])  # 最多 8 条
    if not wechat_content:
        wechat_content = "今日 AI 资讯已更新，详情请查看完整推送"

    push_config = config.get("push", {})

    # Bark（iPhone，可选）
    bark_key = os.environ.get("BARK_KEY")
    if bark_key:
        print(f"\n{'='*50}")
        print(f"  推送摘要到 iPhone...（共 {len(all_summaries)} 个领域）")
        print(f"{'='*50}")
        bark_server_url = push_config.get("bark", {}).get("server_url")
        push_to_bark(bark_key, title, full_content, bark_server_url)
    else:
        print("\n  [SKIP] BARK_KEY 未设置，跳过 Bark 推送")

    # 微信测试号（可选）
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
            appid, secret, template_id, title, wechat_content,
            extra_recipients=extra or None,
            url=digest_url,
        )

    print(f"\n{'='*50}")
    print(f"  完成！今日摘要已推送。")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
