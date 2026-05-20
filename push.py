"""推送模块：Bark（iOS） + 微信测试号（可选）"""

from typing import Optional

import requests

BARK_DEFAULT_URL = "https://api.day.app"


def push_to_bark(
    bark_key: str, title: str, body: str, server_url: Optional[str] = None
) -> bool:
    """通过 Bark 推送通知到 iPhone。

    Args:
        bark_key: Bark App 中显示的设备密钥
        title: 通知标题
        body: 通知正文（支持 Markdown）
        server_url: 自建服务地址，不传则用官方 api.day.app
    """
    base_url = server_url or BARK_DEFAULT_URL
    url = f"{base_url}/{bark_key}"

    payload = {
        "title": title,
        "body": body,
        "group": "每日资讯",
        "sound": "default",
        "icon": "https://cdn-icons-png.flaticon.com/512/1828/1828640.png",
    }

    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") == 200:
            print(f"  [OK] Bark 推送成功")
            return True
        else:
            print(f"  [ERR] Bark 返回异常: {data}")
            return False
    except Exception as e:
        print(f"  [ERR] Bark 推送失败: {e}")
        return False


def _get_access_token(appid: str, secret: str) -> Optional[str]:
    """获取微信 access_token（有效期 2 小时）。"""
    try:
        resp = requests.get(
            "https://api.weixin.qq.com/cgi-bin/token",
            params={"grant_type": "client_credential", "appid": appid, "secret": secret},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if "access_token" in data:
            return data["access_token"]
        print(f"  [ERR] 微信 token 获取失败: {data}")
        return None
    except Exception as e:
        print(f"  [ERR] 微信 token 请求失败: {e}")
        return None


def _get_followers(access_token: str) -> list[str]:
    """拉取测试号的所有关注者 OpenID 列表。"""
    try:
        resp = requests.get(
            "https://api.weixin.qq.com/cgi-bin/user/get",
            params={"access_token": access_token},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if "data" in data and "openid" in data["data"]:
            return data["data"]["openid"]
        print(f"  [WARN] 获取关注列表失败: {data}")
        return []
    except Exception as e:
        print(f"  [ERR] 获取关注列表请求失败: {e}")
        return []


def _send_template(access_token: str, user_id: str, template_id: str, title: str, content: str) -> bool:
    """向单个用户发送模板消息。"""
    try:
        resp = requests.post(
            "https://api.weixin.qq.com/cgi-bin/message/template/send",
            params={"access_token": access_token},
            json={
                "touser": user_id,
                "template_id": template_id,
                "data": {
                    "title": {"value": title, "color": "#173177"},
                    "content": {"value": content, "color": "#000000"},
                },
            },
            timeout=10,
        )
        resp.raise_for_status()
        result = resp.json()
        if result.get("errcode") == 0:
            return True
        else:
            print(f"  [ERR] 推送失败 {user_id[:8]}...: {result}")
            return False
    except Exception as e:
        print(f"  [ERR] 推送请求失败 {user_id[:8]}...: {e}")
        return False


def push_to_wechat_test_account(
    appid: str,
    secret: str,
    template_id: str,
    title: str,
    content: str,
    extra_recipients: Optional[list[str]] = None,
) -> bool:
    """通过微信测试号推送到所有关注者。

    自动拉取所有关注者的 OpenID，无需手动配置。
    extra_recipients 可额外指定不在关注列表里的人（极少用）。
    """
    # 1. 获取 access_token
    access_token = _get_access_token(appid, secret)
    if not access_token:
        return False

    # 2. 自动拉取所有关注者
    user_ids = _get_followers(access_token)
    if not user_ids:
        print(f"  [WARN] 测试号暂无关注者，跳过")
        return False

    # 3. 合并额外接收人
    if extra_recipients:
        extra = [u for u in extra_recipients if u not in user_ids]
        user_ids.extend(extra)

    # 4. 逐个发送
    print(f"  -> 共 {len(user_ids)} 位接收人")
    success = 0
    for user_id in user_ids:
        if _send_template(access_token, user_id, template_id, title, content):
            success += 1

    print(f"  [OK] 微信推送完成：成功 {success}/{len(user_ids)} 人")
    return success > 0
