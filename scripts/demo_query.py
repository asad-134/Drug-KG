from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv # <--- ADD THIS IMPORT

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=True)
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from phase3.qa import build_qa_resources, run_verified_query

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a single QA query using GraphCypherQAChain")
    parser.add_argument("question", help="User question")
    return parser.parse_args()

def main():
    # --- ADD THIS LINE to actually load your .env file ---
     

    if not os.getenv("OPENROUTER_API_KEY"):
        raise SystemExit("OPENROUTER_API_KEY is required in .env")

    args = parse_args()
    resources = build_qa_resources(PROJECT_ROOT)
    answer, resolution = run_verified_query(args.question, resources)
    if resolution.used:
        print(f"Resolved '{resolution.matched_phrase}' to '{resolution.matched_name}'.")
    print(answer)

if __name__ == "__main__":
    main()