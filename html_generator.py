"""把 AI 摘要转成可读的 HTML 页面"""

def generate_html(title: str, sections: list[str]) -> str:
    """生成干净、移动友好的 HTML。"""
    items_html = ""
    for section_text in sections:
        lines = section_text.strip().split("\n")
        lines_html = ""
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith("# "):
                continue  # 跳过顶层标题，用 section 标题代替
            lines_html += f"<p>{_line_to_html(line)}</p>\n"

        # 提取领域名（section_text 第一行是 "# 领域名"）
        heading = "AI / 大模型"
        for line in lines:
            if line.startswith("# "):
                heading = line[2:].strip()
                break

        items_html += f"""
    <div class="section">
      <h2>{heading}</h2>
      {lines_html}
    </div>"""

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>{title}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, "PingFang SC", "Helvetica Neue", sans-serif;
    background: #f5f5f5;
    color: #333;
    padding: 16px;
    line-height: 1.7;
  }}
  .container {{ max-width: 680px; margin: 0 auto; }}
  h1 {{
    font-size: 20px;
    font-weight: 600;
    color: #1a1a1a;
    margin-bottom: 4px;
  }}
  .date {{
    font-size: 14px;
    color: #888;
    margin-bottom: 20px;
  }}
  .section {{
    background: #fff;
    border-radius: 12px;
    padding: 16px 18px;
    margin-bottom: 12px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  }}
  .section h2 {{
    font-size: 16px;
    font-weight: 600;
    color: #1a1a1a;
    margin-bottom: 10px;
    padding-bottom: 8px;
    border-bottom: 2px solid #e8e8e8;
  }}
  .section p {{
    font-size: 15px;
    color: #444;
    margin-bottom: 8px;
    padding-left: 4px;
  }}
  a {{
    color: #007aff;
    text-decoration: none;
    font-size: 13px;
  }}
  a:hover {{ text-decoration: underline; }}
  .footnote {{
    text-align: center;
    font-size: 12px;
    color: #aaa;
    margin-top: 24px;
    padding-bottom: 32px;
  }}
</style>
</head>
<body>
<div class="container">
  <h1>{title}</h1>
  <p class="date">每日资讯 · AI 领域</p>
  {items_html}
  <p class="footnote">由 DeepSeek 自动整理 · 仅供参考</p>
</div>
</body>
</html>"""


def generate_article_html(title: str, sections: list[str]) -> str:
    """生成适合微信公众号图文消息的 HTML 正文（无外部 CSS，纯内容结构）。

    微信公众号的正文渲染有自己的样式表，我们只输出内容标签。
    """
    items_html = ""
    for section_text in sections:
        lines = section_text.strip().split("\n")
        heading = "AI / 大模型"
        content_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith("# "):
                heading = line[2:].strip()
                continue
            content_lines.append(f"<p>{_line_to_html(line)}</p>")

        items_html += f"<h2>{heading}</h2>\n{''.join(content_lines)}\n"

    return (
        f"<h1>{title}</h1>\n"
        f'<p style="color:#888;font-size:14px;margin-bottom:20px">每日资讯 · AI 领域</p>\n'
        f"{items_html}"
        f'<hr style="border:none;border-top:1px solid #eee;margin:30px 0">\n'
        f'<p style="color:#aaa;font-size:12px;text-align:center">由 DeepSeek 自动整理 · 仅供参考</p>'
    )


def _line_to_html(line: str) -> str:
    """把一行 Markdown 转成 HTML 片段。"""
    # Markdown 链接 [text](url) → <a href="url">text</a>
    import re
    line = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank" rel="noopener">\1</a>', line)
    # 加粗 **text** → <strong>text</strong>
    line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
    return line
