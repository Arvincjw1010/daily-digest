"""每日资讯摘要：采集 -> AI 整理 -> 保存（不推送，推送由 notify.py 执行）"""

import json
import os
import sys
from datetime import date

import yaml
from dotenv import load_dotenv

from search import search_interest
from summarize import summarize_interest
from html_generator import generate_html


def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def main():
    load_dotenv()
    config = load_config()

    deepseek_api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not deepseek_api_key:
        print("[FATAL] 环境变量 DEEPSEEK_API_KEY 未设置")
        sys.exit(1)

    deepseek_model = config.get("deepseek", {}).get("model", "deepseek-chat")
    push_config = config.get("push", {})
    wechat_config = push_config.get("wechat", {})

    all_summaries = []

    # ---- 阶段 1：采集 + 整理 ----
    for interest in config["interests"]:
        name = interest["name"]
        print(f"\n{'='*50}")
        print(f"  领域: {name}")
        print(f"{'='*50}")

        results = search_interest(interest)
        if not results:
            print(f"  -> '{name}' 无内容，跳过")
            continue

        print(f"  [AI] 正在用 DeepSeek 整理...")
        summary = summarize_interest(name, results, deepseek_api_key, deepseek_model)
        if summary:
            all_summaries.append(f"# {name}\n\n{summary}")

    if not all_summaries:
        print("\n没有内容，退出。")
        return

    today = date.today().isoformat()
    title = f"每日资讯 · {today}"
    full_content = "\n\n---\n\n".join(all_summaries)

    # ---- 生成 HTML ----
    digest_url = None
    try:
        html = generate_html(title, all_summaries)
        os.makedirs("public", exist_ok=True)
        with open("public/index.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("  [OK] HTML 页面已生成: public/index.html")
        digest_url = None  # 不加链接，内容直接写卡片里
    except Exception as e:
        print(f"  [WARN] HTML 生成失败: {e}")

    # ---- 为微信生成紧凑版（直接包含摘要正文） ----
    import re as _re
    wechat_content = ""
    for summary in all_summaries:
        # 去掉 # 标题
        text = _re.sub(r'^#+\s*', '', summary, flags=_re.MULTILINE)
        # 去掉 ** 加粗
        text = text.replace('**', '')
        # 去掉 Markdown 链接标记: [text](url) -> text
        text = _re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        # 去掉 --- 分隔线
        text = _re.sub(r'^---+$', '', text, flags=_re.MULTILINE)
        # 合并多余空行
        text = _re.sub(r'\n{3,}', '\n\n', text)
        # 每行开头缩进
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        text = '\n'.join(lines)
        wechat_content += text + '\n\n'

    wechat_content = wechat_content.strip()
    # 限制总长度（微信显示大约 600-800 字比较稳妥）
    if len(wechat_content) > 600:
        wechat_content = wechat_content[:597] + '...'

    # ---- 把所有推送信息存成 JSON（notify.py 会读） ----
    payload = {
        "title": title,
        "full_content": full_content,
        "wechat_content": wechat_content,
        "digest_url": digest_url,
        "bark_key": os.environ.get("BARK_KEY"),
        "bark_server_url": (push_config.get("bark") or {}).get("server_url"),
        "wechat_enabled": wechat_config.get("enabled", False),
        "wechat_appid_env": wechat_config.get("appid_env", "WECHAT_APPID"),
        "wechat_secret_env": wechat_config.get("secret_env", "WECHAT_SECRET"),
        "wechat_template_id_env": wechat_config.get("template_id_env", "WECHAT_TEMPLATE_ID"),
        "wechat_recipients": wechat_config.get("recipients", []),
    }

    with open("notify_payload.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print("  [OK] 推送数据已保存到 notify_payload.json")

    print(f"\n{'='*50}")
    print(f"  生成完成！等待 notify.py 推送。")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
