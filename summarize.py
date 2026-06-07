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

    # 根据兴趣类型定制 prompt
    if "产品" in interest_name:
        angle = """你是一个关注大模型产品动态的分析师。下面是一组今天的 AI 行业原始信息。

你的任务是筛选和整理：
1. **只保留产品相关的信息**：新功能发布、模型升级、API 变更、定价调整、产品下线/合并
2. **扔掉无关内容**：纯学术论文、企业融资新闻（除非涉及产品）、泛泛的行业预测
3. **每条写法的要求**：
   - 标题：一句话说清楚「谁 + 做了什么 + 为什么值得关注」
   - 摘要 2-3 句：这条更新对我有什么影响？我需要知道什么？
   - 末尾附带原文链接（Markdown 格式）
4. **按重要程度排序**：ChatGPT/Claude/Gemini 等主流产品优先，小众工具放后面
5. **去重合并**：同一事件多家报道合并为一条

输出格式（严格 Markdown）：
- **OpenAI 发布 GPT-5 API，价格下调 50%**：今日起 GPT-5 的 API 调用费用减半，同时新增了函数调用的流式支持... [来源](https://...)
- **Claude 推出团队协作空间**：Anthropic 为 Claude 企业版增加了共享工作区功能... [来源](https://...)"""
    elif "国内" in interest_name:
        angle = """你是一个关注中国 AI 行业动态的观察者。下面是一组今天的中文 AI 资讯原始信息。

你的任务是筛选和整理：
1. **值得关注的内容类型**：
   - 国产大模型发布/更新（DeepSeek、文心一言、通义千问、豆包、Kimi、智谱、百川等）
   - AI 应用落地案例（国内公司的实际部署和使用场景）
   - 行业政策与监管动向（有实质影响的新规、牌照、扶持政策）
   - 芯片/算力相关重大进展
   - 国内 AI 创业公司融资或重要产品发布
2. **扔掉的内容**：
   - 纯翻译/搬运外媒报道（除非有独家解读）
   - 软文/广告/付费推广
   - 活动预告/直播预告/早报晚报日报汇总
   - 泛泛的行业趋势分析（没有具体信息）
3. **每条写法**：
   - 标题：谁 + 做了什么 + 为什么重要
   - 摘要 2-3 句中文：核心信息和影响
   - 末尾附带原文链接
4. **按重要性和信息密度排序**
5. **去重合并**：同一事件多家报道合并为一条

输出格式（严格 Markdown）：
- **DeepSeek 发布 V3 模型，推理成本再降 50%**：DeepSeek 今日更新了 V3 版本，API 价格下调，同时在多轮对话能力上有显著提升... [来源](https://...)
- **字节豆包大模型日调用量突破 5000 亿**：字节跳动披露豆包大模型的最新数据，日调用量相比上季度翻倍... [来源](https://...)"""
    else:
        angle = """你是一个关注 AI 创意应用和有趣工具的观察者。下面是一组今天与 AI 相关的原始信息。

你的任务是：
1. **只保留新奇好玩的内容**：新出的 AI 工具、让人眼前一亮的使用案例、有趣的实验和 demo、社区里的热门讨论
2. **扔掉**：干巴巴的产品公告、融资新闻、学术论文、重复报道
3. **每条写法**：
   - 标题：名字或玩法 + 一句话亮点
   - 摘要 2-3 句：这个工具/项目做了什么？为什么有趣？我可以怎么试？
   - 末尾附带原文链接（Markdown 格式）
4. **按趣味性和实用性排序**：让人想立刻去试的排前面
5. **去重合并**：同一项目被多方讨论的合并为一条

输出格式（严格 Markdown）：
- **Open-Sora 2.0 发布，消费级显卡可跑视频生成**：清华大学团队开源的视频生成模型更新，RTX 4090 即可运行... [来源](https://...)
- **开发者用 Claude 写了一个自动修 Bug 的 GitHub Action**：一位独立开发者分享了用 Claude API 搭建的自动修复工具... [来源](https://...)"""

    return f"""{angle}

⚠️ 重要：不相关的内容直接跳过，宁可少而精。如果所有原始信息都不相关，回复「今日无值得关注的内容」即可，不要硬凑。

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
            max_tokens=4096,
        )
        return resp.choices[0].message.content or ""
    except Exception as e:
        print(f"  [ERROR] DeepSeek API 调用失败: {e}")
        return ""
