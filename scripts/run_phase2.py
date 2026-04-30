from __future__ import annotations

# pyright: reportMissingImports=false

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from phase2.config import default_config
from phase2.pipeline import run_phase2
from phase2.validate import run_validation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Phase 2 graph export and validation pipeline"
    )
    parser.add_argument(
        "--project-root",
        default=str(PROJECT_ROOT),
        help="Path to project root (defaults to current repository root)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = default_config(args.project_root)
    result = run_phase2(config)
    validation = run_validation(config)

    print("Phase 2 complete.")
    print(f"Graph outputs: {result.graph_dir}")
    print(f"Validation outputs: {result.validation_dir}")
    print(f"Stats file: {result.stats_path}")
    print(f"Validation report: {validation.report_path}")


if __name__ == "__main__":
    main()
