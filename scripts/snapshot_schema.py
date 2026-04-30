from __future__ import annotations

# pyright: reportMissingImports=false

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from phase3.config import default_config
from phase3.schema_snapshot import snapshot_schema


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Snapshot Neo4j schema for Phase 3")
    parser.add_argument(
        "--project-root",
        default=str(PROJECT_ROOT),
        help="Path to project root (defaults to current repository root)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = default_config(args.project_root)
    output_path = snapshot_schema(config.schema_snapshot_path)
    print(f"Schema snapshot written to: {output_path}")


if __name__ == "__main__":
    main()
