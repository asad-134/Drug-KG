from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class Phase1Config:
    project_root: Path
    input_dir: Path = field(init=False)
    output_dir: Path = field(init=False)
    staging_dir: Path = field(init=False)
    profiling_dir: Path = field(init=False)
    mapping_doc_path: Path = field(init=False)

    target_sections: tuple[str, ...] = (
        "indications_and_usage",
        "adverse_reactions",
        "drug_interactions",
        "contraindications",
        "warnings_and_cautions",
        "boxed_warning",
    )

    def __post_init__(self) -> None:
        self.input_dir = self.project_root / "drug-labels"
        self.output_dir = self.project_root / "outputs" / "phase1"
        self.staging_dir = self.output_dir / "staging"
        self.profiling_dir = self.output_dir / "profiling"
        self.mapping_doc_path = self.output_dir / "openfda_field_mapping.md"

    def ensure_dirs(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.staging_dir.mkdir(parents=True, exist_ok=True)
        self.profiling_dir.mkdir(parents=True, exist_ok=True)


def default_config(project_root: str | Path = ".") -> Phase1Config:
    return Phase1Config(project_root=Path(project_root).resolve())
