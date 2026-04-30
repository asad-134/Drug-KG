from __future__ import annotations

import os
import re
from dataclasses import dataclass


PRESCRIPTIVE_PATTERNS = [
    r"\byou should\b",
    r"\byou must\b",
    r"\bstart taking\b",
    r"\bstop taking\b",
    r"\bincrease (the )?dose\b",
    r"\bdecrease (the )?dose\b",
    r"\bmg\b",
]


@dataclass(slots=True)
class SafetyResult:
    allowed: bool
    reason: str | None
    sanitized_text: str


def get_disclaimer() -> str:
    return os.getenv(
        "SAFETY_DISCLAIMER",
        "This information is for educational purposes only and is not medical advice. "
        "Consult a qualified healthcare professional.",
    )


def validate_response(text: str) -> SafetyResult:
    lowered = text.lower()
    for pattern in PRESCRIPTIVE_PATTERNS:
        if re.search(pattern, lowered):
            disclaimer = get_disclaimer()
            return SafetyResult(
                allowed=False,
                reason=f"Matched restricted pattern: {pattern}",
                sanitized_text=f"I can't provide medical advice. {disclaimer}",
            )

    disclaimer = get_disclaimer()
    if disclaimer.lower() not in lowered:
        text = f"{text.strip()}\n\n{disclaimer}"

    return SafetyResult(allowed=True, reason=None, sanitized_text=text)
