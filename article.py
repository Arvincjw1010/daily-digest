"""微信公众号图文消息发布：创建草稿 → 发布 → 获取文章链接"""

import base64
import time
from typing import Optional

import requests

# 1x1 蓝色像素 PNG（base64 编码，无需依赖图片库）
_COVER_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ"
    "AAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


def _get_access_token(appid: str, secret: str) -> Optional[str]:
    try:
        resp = requests.get(
            "https://api.weixin.qq.com/cgi-bin/token",
            params={
                "grant_type": "client_credential",
                "appid": appid,
                "secret": secret,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if "access_token" in data:
            return data["access_token"]
        print(f"  [ERR] token 获取失败: {data}")
        return None
    except Exception as e:
        print(f"  [ERR] token 请求失败: {e}")
        return None


def _upload_cover(access_token: str) -> Optional[str]:
    """上传封面图（永久素材），返回 media_id。"""
    try:
        img_data = base64.b64decode(_COVER_PNG_B64)
        resp = requests.post(
            "https://api.weixin.qq.com/cgi-bin/material/add_material",
            params={"access_token": access_token, "type": "image"},
            files={"media": ("cover.png", img_data, "image/png")},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        if "media_id" in data:
            print(f"  [OK] 封面上传成功")
            return data["media_id"]
        print(f"  [ERR] 封面上传失败: {data}")
        return None
    except Exception as e:
        print(f"  [ERR] 封面上传请求失败: {e}")
        return None


def _create_draft(
    access_token: str, title: str, content: str, thumb_media_id: str
) -> Optional[str]:
    """创建草稿，返回 media_id。"""
    try:
        resp = requests.post(
            "https://api.weixin.qq.com/cgi-bin/draft/add",
            params={"access_token": access_token},
            json={
                "articles": [
                    {
                        "title": title,
                        "author": "",
                        "digest": content[:80].replace("\n", " ").strip(),
                        "content": content,
                        "content_source_url": "",
                        "thumb_media_id": thumb_media_id,
                        "need_open_comment": 0,
                        "only_fans_can_comment": 0,
                    }
                ]
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        if "media_id" in data:
            print(f"  [OK] 草稿创建成功")
            return data["media_id"]
        print(f"  [ERR] 草稿创建失败: {data}")
        return None
    except Exception as e:
        print(f"  [ERR] 草稿创建请求失败: {e}")
        return None


def _publish_draft(access_token: str, media_id: str) -> Optional[str]:
    """发布草稿并轮询获取文章 URL（最长等 30 秒）。"""
    try:
        resp = requests.post(
            "https://api.weixin.qq.com/cgi-bin/freepublish/submit",
            params={"access_token": access_token},
            json={"media_id": media_id},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("errcode") != 0:
            print(f"  [ERR] 发布提交失败: {data}")
            return None
        publish_id = data.get("publish_id")
        print(f"  [OK] 发布已提交")
    except Exception as e:
        print(f"  [ERR] 发布提交请求失败: {e}")
        return None

    for i in range(10):
        time.sleep(3)
        try:
            resp = requests.get(
                "https://api.weixin.qq.com/cgi-bin/freepublish/get",
                params={
                    "access_token": access_token,
                    "publish_id": publish_id,
                },
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            status = data.get("publish_status", -1)
            # 0=发布成功, 1=发布中
            if status == 0:
                articles = data.get("article_detail", {}).get("item", [])
                if articles and "article_url" in articles[0]:
                    url = articles[0]["article_url"]
                    print(f"  [OK] 文章已发布: {url}")
                    return url
                print(f"  [WARN] 发布成功但未获取到 URL: {data}")
                return None
            elif status == 1:
                print(f"  [WAIT] 发布中... ({i+1}/10)")
                continue
            else:
                print(f"  [WARN] 发布状态异常: {data}")
                return None
        except Exception as e:
            print(f"  [ERR] 查询发布状态失败: {e}")
            return None

    print(f"  [ERR] 发布超时")
    return None


def publish_article(
    appid: str, secret: str, title: str, html_content: str
) -> Optional[str]:
    """完整流程：上传封面 → 创建草稿 → 发布 → 返回文章 URL。"""
    print(f"\n  [公众号] 开始发布图文文章...")

    access_token = _get_access_token(appid, secret)
    if not access_token:
        return None

    thumb_id = _upload_cover(access_token)
    if not thumb_id:
        return None

    media_id = _create_draft(access_token, title, html_content, thumb_id)
    if not media_id:
        return None

    url = _publish_draft(access_token, media_id)
    if url:
        print(f"  [公众号] 文章链接: {url}")
    else:
        print(f"  [WARN] 文章发布失败")
    return url
