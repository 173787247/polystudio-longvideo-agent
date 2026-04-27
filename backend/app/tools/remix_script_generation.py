from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class RemixScriptRequest:
    analysis: Dict[str, Any]
    target_style: str = "news_anchor"


def generate_remix_script_tool(req: RemixScriptRequest) -> str:
    """
    脚本生成（mock 版）：把理解结果结构化字段填入固定模板。

    真实接入时：可替换为 LLM 调用，但输入/输出形状保持不变，便于被 Skill 强约束编排。
    """
    a = req.analysis
    duration = a.get("duration_s")
    size = a.get("size")
    fps = a.get("fps")
    keyframes: List[str] = list(a.get("keyframes") or [])

    title = "视频要点速报"
    lead = "下面为你带来一段内容二创后的新闻播报式解读。"
    bullets = [
        f"素材时长约 {duration if duration is not None else '未知'} 秒，帧率约 {fps if fps is not None else '未知'}。",
        f"画面尺寸 {size if size is not None else '未知'}，已抽取 {len(keyframes)} 张关键帧作为视觉提示。",
        "基于关键帧与元信息，对内容进行结构化重写与要点提炼。",
    ]

    ending = "以上就是本次速报，我们下条见。"

    if req.target_style != "news_anchor":
        # 允许扩展风格，但仍保持“可播报”的结构
        title = f"二创脚本（{req.target_style}）"

    body = "\n".join(f"- {x}" for x in bullets)
    return (
        f"【标题】{title}\n"
        f"【导语】{lead}\n"
        f"【要点】\n{body}\n"
        f"【结尾】{ending}\n"
    )

