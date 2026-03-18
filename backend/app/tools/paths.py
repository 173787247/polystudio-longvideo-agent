from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    project_root: Path

    @property
    def outputs_dir(self) -> Path:
        return self.project_root / "outputs"

    def ensure_outputs_dir(self) -> Path:
        out = self.outputs_dir
        out.mkdir(parents=True, exist_ok=True)
        return out


def resolve_project_paths() -> ProjectPaths:
    # backend/app/tools/paths.py -> project root = ../../..
    root = Path(__file__).resolve().parents[3]
    return ProjectPaths(project_root=root)

