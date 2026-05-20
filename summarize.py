"""AI 整理模块：用 DeepSeek 对原始内容进行去重、排序和摘要"""

from openai import OpenAI

DEEPSEEK_BASE_URL = "https://api.deepseek.com"


def _build_prompt(interest_name: str, results: list[dict]) -> str:
    items_text = ""
    for i, r in enumerate(results, 1):
        items_text += (
            f"[{i}] {r['title']}\n"
            f"   {r['content'][:300]}\n"
            f"   原文链接: {r['url']}\n\n"
        )

    return f"""你是一个专业的资讯整理助手。请将以下关于「{interest_name}」的搜索结果，整理成一份清晰、可读的每日摘要。

要求：
1. 去重合并：相同事件的不同报道合并为一条
2. 每条写 2-3 句中文摘要，保留核心信息
3. 按重要性从高到低排序
4. 每条末尾保留原文链接（Markdown 格式）

输出格式：
- **标题**：摘要内容... [来源](链接)

原始搜索结果：
{items_text}
请输出整理后的摘要："""


def summarize_interest(
    interest_name: str,
    results: list[dict],
    api_key: str,
    model: str = "deepseek-chat",
) -> str:
    """调用 DeepSeek API 整理摘要，返回 Markdown 文本。"""
    if not results:
        return ""

    client = OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)
    prompt = _build_prompt(interest_name, results)

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2048,
        )
        return resp.choices[0].message.content or ""
    except Exception as e:
        print(f"  [ERROR] DeepSeek API 调用失败: {e}")
        return ""
