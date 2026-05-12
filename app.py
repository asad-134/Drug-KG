from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env", override=True)

SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from phase3.qa import build_qa_resources, run_verified_query


@st.cache_resource
def get_resources():
    return build_qa_resources(PROJECT_ROOT)


def main() -> None:
    st.set_page_config(page_title="Drug KG QA", page_icon="💊", layout="centered")
    st.title("Drug Knowledge Graph QA")
    st.caption(
        "Educational use only. This tool does not provide medical advice, diagnosis, or treatment."
    )

    question = st.text_input(
        "Ask a question",
        placeholder="What drugs treat hypertension?",
    )
    submit = st.button("Run query", type="primary", use_container_width=True)

    if submit:
        if not question.strip():
            st.warning("Please enter a question.")
            return

        if not os.getenv("OPENROUTER_API_KEY"):
            st.error("OPENROUTER_API_KEY is not configured.")
            return

        with st.spinner("Querying the graph and generating response..."):
            try:
                resources = get_resources()
                answer, resolution = run_verified_query(question, resources)
                if resolution.used:
                    st.caption(
                        f"Resolved '{resolution.matched_phrase}' to '{resolution.matched_name}'."
                    )
                st.markdown(answer)
            except Exception as exc:
                st.error(f"Request failed: {exc}")


if __name__ == "__main__":
    main()
