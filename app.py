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

from phase3.llm_chain import build_graph_chain
from phase3.safety import validate_response


@st.cache_resource
def get_chain():
    return build_graph_chain(PROJECT_ROOT)


def main() -> None:
    st.set_page_config(page_title="Drug KG QA", page_icon="💊", layout="centered")
    st.title("Drug Knowledge Graph QA")
    st.caption(
        "Educational use only. This tool does not provide medical advice, diagnosis, or treatment."
    )

    preset_questions = [
        "What is gabapentin used for?",
        "Does gabapentin interact with morphine?",
        "What are the serious warnings for varenicline?",
        "What drugs interact with warfarin?",
        "Does varenicline interact with alcohol?",
        "Can children take gabapentin?",
        "What is the half-life of gabapentin?",
        "Does glimepiride cause hypoglycemia?",
        "What is varenicline's mechanism of action?",
    ]

    st.subheader("Quick queries")
    selected_preset = None
    cols = st.columns(2)
    for idx, preset in enumerate(preset_questions):
        col = cols[idx % 2]
        if col.button(preset, use_container_width=True):
            selected_preset = preset

    question = st.text_input(
        "Ask a question",
        placeholder="What drugs treat hypertension?",
        value=selected_preset or "",
    )
    submit = st.button("Run query", type="primary", use_container_width=True)

    if submit or selected_preset:
        if not question.strip():
            st.warning("Please enter a question.")
            return

        if not os.getenv("OPENROUTER_API_KEY"):
            st.error("OPENROUTER_API_KEY is not configured.")
            return

        with st.spinner("Querying the graph and generating response..."):
            try:
                chain = get_chain()
                response = chain.invoke({"query": question})
                text = response.get("result", "") if isinstance(response, dict) else str(response)
                safety = validate_response(text)
                st.markdown(safety.sanitized_text)
            except Exception as exc:
                st.error(f"Request failed: {exc}")


if __name__ == "__main__":
    main()
