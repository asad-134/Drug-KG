from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Generator


def shard_paths(input_dir: Path) -> list[Path]:
    return sorted(input_dir.glob("drug-label-*-of-*.json"))


def iter_records(input_dir: Path) -> Generator[dict[str, Any], None, None]:
    for shard in shard_paths(input_dir):
        with shard.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        if isinstance(payload, list):
            records = payload
        else:
            records = payload.get("results", [])

        for record in records:
            record["_shard"] = shard.name
            yield record
