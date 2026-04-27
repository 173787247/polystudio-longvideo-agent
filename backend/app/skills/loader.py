from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SkillInfo:
    name: str
    skill_md_path: Path
    description: str


class SkillsLoader:
    """
    极简 Skill 发现与按需加载（Progressive Loading）：
    - 常驻上下文：仅暴露 name/description/path 的摘要（低 token）
    - 触发后：再读取完整 SKILL.md 内容（高 token）
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.skills_dir = project_root / "skills"

    def list_skills(self) -> list[SkillInfo]:
        if not self.skills_dir.exists():
            return []

        out: list[SkillInfo] = []
        for d in sorted(self.skills_dir.iterdir()):
            if not d.is_dir():
                continue
            p = d / "SKILL.md"
            if not p.exists():
                continue
            name, desc = _read_frontmatter_name_desc(p)
            out.append(SkillInfo(name=name or d.name, skill_md_path=p, description=desc or ""))
        return out

    def build_skills_summary_xml(self) -> str:
        skills = self.list_skills()
        if not skills:
            return ""

        def esc(s: str) -> str:
            return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        lines = ["<skills>"]
        for s in skills:
            lines.append("  <skill>")
            lines.append(f"    <name>{esc(s.name)}</name>")
            lines.append(f"    <description>{esc(s.description)}</description>")
            lines.append(f"    <location>{esc(str(s.skill_md_path))}</location>")
            lines.append("  </skill>")
        lines.append("</skills>")
        return "\n".join(lines)

    def load_skill_body(self, name: str) -> str | None:
        for s in self.list_skills():
            if s.name == name or s.skill_md_path.parent.name == name:
                return s.skill_md_path.read_text(encoding="utf-8")
        return None


def _read_frontmatter_name_desc(path: Path) -> tuple[str | None, str | None]:
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("---"):
        return None, None

    m = re.match(r"^---\n(.*?)\n---\n", raw, re.DOTALL)
    if not m:
        return None, None

    name: str | None = None
    desc: str | None = None
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        k = k.strip()
        v = v.strip().strip('"\'')
        if k == "name":
            name = v
        elif k == "description":
            desc = v
    return name, desc

