from __future__ import annotations

from pathlib import Path


def load_system_prompt(project_root: Path) -> str:
    prompt_path = project_root / "prompts" / "safety_system_prompt.txt"
    return prompt_path.read_text(encoding="utf-8")
