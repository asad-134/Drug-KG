from __future__ import annotations

# pyright: reportMissingImports=false

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from phase1.config import default_config
from phase1.pipeline import run_phase1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Phase 1 OpenFDA profiling and staging pipeline"
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
    result = run_phase1(config)
    print(f"Phase 1 complete. Records processed: {result.total_records}")
    print(f"Outputs written to: {result.output_dir}")


if __name__ == "__main__":
    main()
