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

from phase3.llm_chain import build_graph_chain
from phase3.safety import validate_response

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a single QA query using GraphCypherQAChain")
    parser.add_argument("question", help="User question")
    return parser.parse_args()

def main():
    # --- ADD THIS LINE to actually load your .env file ---
     

    if not os.getenv("OPENROUTER_API_KEY"):
        raise SystemExit("OPENROUTER_API_KEY is required in .env")

    args = parse_args()
    chain = build_graph_chain(PROJECT_ROOT)
    response = chain.invoke({"query": args.question})
    text = response.get("result", "") if isinstance(response, dict) else str(response)

    safety = validate_response(text)
    print(safety.sanitized_text)

if __name__ == "__main__":
    main()