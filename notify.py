"""读取 main.py 生成的推送数据并发送通知（在 HTML 提交到 GitHub 之后执行）"""

import json
import os
import sys

from push import push_to_bark, push_to_wechat_test_account


def get_env_or_exit(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        print(f"[FATAL] 环境变量 {name} 未设置")
        sys.exit(1)
    return value


def main():
    if not os.path.exists("notify_payload.json"):
        print("[FATAL] 未找到 notify_payload.json，请先运行 main.py")
        sys.exit(1)

    with open("notify_payload.json", "r", encoding="utf-8") as f:
        p = json.load(f)

    title = p["title"]
    full_content = p["full_content"]
    wechat_content = p["wechat_content"]
    digest_url = p.get("digest_url")

    # Bark
    bark_key = p.get("bark_key")
    if bark_key:
        print(f"\n{'='*50}")
        print("  推送摘要到 iPhone...")
        print(f"{'='*50}")
        push_to_bark(bark_key, title, full_content, p.get("bark_server_url"))
    else:
        print("\n  [SKIP] BARK_KEY 未设置，跳过 Bark 推送")

    # 微信测试号
    if p.get("wechat_enabled"):
        print(f"\n{'='*50}")
        print("  推送到微信测试号...")
        print(f"{'='*50}")
        appid = get_env_or_exit(p["wechat_appid_env"])
        secret = get_env_or_exit(p["wechat_secret_env"])
        template_id = get_env_or_exit(p["wechat_template_id_env"])
        extra = p.get("wechat_recipients", [])
        push_to_wechat_test_account(
            appid, secret, template_id, title, wechat_content,
            extra_recipients=extra or None,
            url=digest_url,
        )

    print(f"\n{'='*50}")
    print(f"  通知推送完成！")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
