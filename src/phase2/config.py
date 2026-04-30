from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class Phase2Config:
    project_root: Path
    phase1_output_dir: Path = field(init=False)
    phase2_output_dir: Path = field(init=False)
    graph_dir: Path = field(init=False)
    validation_dir: Path = field(init=False)

    def __post_init__(self) -> None:
        self.phase1_output_dir = self.project_root / "outputs" / "phase1"
        self.phase2_output_dir = self.project_root / "outputs" / "phase2"
        self.graph_dir = self.phase2_output_dir / "graph"
        self.validation_dir = self.phase2_output_dir / "validation"

    @property
    def staging_dir(self) -> Path:
        return self.phase1_output_dir / "staging"

    def ensure_dirs(self) -> None:
        self.phase2_output_dir.mkdir(parents=True, exist_ok=True)
        self.graph_dir.mkdir(parents=True, exist_ok=True)
        self.validation_dir.mkdir(parents=True, exist_ok=True)


def default_config(project_root: str | Path = ".") -> Phase2Config:
    return Phase2Config(project_root=Path(project_root).resolve())
