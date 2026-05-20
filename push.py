"""推送模块：仅 Bark（iOS 通知）"""

import requests

BARK_URL = "https://api.day.app"


def push_to_bark(key: str, title: str, body: str) -> bool:
    """推送到 iPhone（Markdown 排版，完整内容）。"""
    try:
        resp = requests.post(
            f"{BARK_URL}/{key}",
            json={
                "title": title,
                "body": body,
                "group": "每日资讯",
                "sound": "default",
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") == 200:
            print(f"  [OK] 已推送到 iPhone")
            return True
        print(f"  [ERR] Bark 返回异常: {data}")
        return False
    except Exception as e:
        print(f"  [ERR] 推送失败: {e}")
        return False
