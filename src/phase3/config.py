from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(slots=True)
class Phase3Config:
    project_root: Path

    def __post_init__(self) -> None:
        load_dotenv(self.project_root / ".env")

    @property
    def outputs_dir(self) -> Path:
        return self.project_root / "outputs" / "phase3"

    @property
    def schema_snapshot_path(self) -> Path:
        return self.outputs_dir / "neo4j_schema_snapshot.json"


def default_config(project_root: str | Path = ".") -> Phase3Config:
    return Phase3Config(project_root=Path(project_root).resolve())
