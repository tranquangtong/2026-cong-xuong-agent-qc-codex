from __future__ import annotations

import difflib
import re


US_TO_UK = {
    "color": "colour",
    "colors": "colours",
    "organize": "organise",
    "organized": "organised",
    "organizing": "organising",
    "behavior": "behaviour",
    "prioritizing": "prioritising",
    "prioritize": "prioritise",
    "analyze": "analyse",
    "license": "licence",
}

QUOTE_PATTERN = re.compile(r"['\"]([^'\"]+)['\"]")


def compare_text(left: str, right: str) -> str:
    diff = difflib.unified_diff(
        left.splitlines(),
        right.splitlines(),
        fromfile="expected",
        tofile="actual",
        lineterm="",
    )
    return "\n".join(diff)


def make_finding_id(prefix: str, index: int) -> str:
    return f"{prefix}-{index:03d}"


def extract_quoted_labels(text: str) -> list[str]:
    return [match.strip() for match in QUOTE_PATTERN.findall(text) if match.strip()]


def check_british_english(text: str) -> list[dict[str, str]]:
    findings = []
    words = re.findall(r"\b[\w-]+\b", text.lower())
    for word in words:
        if word in US_TO_UK:
            findings.append(
                {
                    "evidence": f"Detected US English variant '{word}'.",
                    "recommended_fix": f"Use the British English form '{US_TO_UK[word]}' instead.",
                }
            )
    return findings


def check_spelling(text: str) -> list[dict[str, str]]:
    return check_british_english(text)
