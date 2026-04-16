from __future__ import annotations

from core.content_sources import summarize_content_sources
from core.knowledge import get_knowledge_context
from core.llm import invoke_multimodal_model, invoke_text_model, is_llm_enabled, parse_json_object
from core.state import AgentState, ContentSource, QAFinding
from core.utils import log_communication
from tools.text_tools import check_british_english, extract_quoted_labels, make_finding_id


MAX_CHUNK_CHARS = 4500


def _build_finding(
    prefix: str,
    index: int,
    severity: str,
    area: str,
    evidence: str,
    impact: str,
    fix: str,
    source_agent: str,
) -> QAFinding:
    return {
        "id": make_finding_id(prefix, index),
        "severity": severity,
        "area": area,
        "evidence": evidence,
        "impact": impact,
        "recommended_fix": fix,
        "source_agent": source_agent,
    }


def _source_label(source: ContentSource) -> str:
    return source.get("display_name", source.get("uri", "source"))


def _source_warning_findings(sources: list[ContentSource]) -> list[QAFinding]:
    findings: list[QAFinding] = []
    index = 1
    for source in sources:
        label = _source_label(source)
        for warning in source.get("warnings", []):
            findings.append(
                _build_finding(
                    "C",
                    index,
                    "Info",
                    "Content Source",
                    f"{label}: {warning}",
                    "Content QA coverage is limited until the source can be resolved or extracted successfully.",
                    "Provide a text-based artifact, install the missing parser dependency, or pre-resolve the Figma frame before rerunning content QA.",
                    "content",
                )
            )
            index += 1
    return findings


def _split_text_chunks(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    cleaned = text.strip()
    if not cleaned:
        return []
    if len(cleaned) <= max_chars:
        return [cleaned]

    chunks: list[str] = []
    current: list[str] = []
    current_length = 0
    for line in cleaned.splitlines():
        line_length = len(line) + 1
        if current and current_length + line_length > max_chars:
            chunks.append("\n".join(current).strip())
            current = [line]
            current_length = line_length
            continue
        current.append(line)
        current_length += line_length
    if current:
        chunks.append("\n".join(current).strip())
    return [chunk for chunk in chunks if chunk]


def _renumber_findings(findings: list[QAFinding]) -> list[QAFinding]:
    numbered: list[QAFinding] = []
    for index, finding in enumerate(findings, start=1):
        updated = dict(finding)
        updated["id"] = make_finding_id("C", index)
        numbered.append(updated)
    return numbered


def _dedupe_findings(findings: list[QAFinding]) -> list[QAFinding]:
    deduped: list[QAFinding] = []
    seen: set[tuple[str, str, str, str]] = set()
    for finding in findings:
        key = (
            str(finding.get("severity", "")).strip().lower(),
            str(finding.get("area", "")).strip().lower(),
            str(finding.get("evidence", "")).strip().lower(),
            str(finding.get("recommended_fix", "")).strip().lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(finding)
    return _renumber_findings(deduped)


def _fallback_text_findings(text: str) -> list[QAFinding]:
    lowered = text.lower()
    findings: list[QAFinding] = []
    content_index = 1

    if " user " in f" {lowered} ":
        findings.append(
            _build_finding(
                "C",
                content_index,
                "Major",
                "Terminology",
                "Detected the term 'User' in the supplied content.",
                "Project terminology expects 'Learner' instead of 'User'.",
                "Replace 'User' with 'Learner' throughout the affected content.",
                "content",
            )
        )
        content_index += 1

    for issue in check_british_english(text):
        findings.append(
            _build_finding(
                "C",
                content_index,
                "Minor",
                "Grammar/Spelling",
                issue["evidence"],
                "Mixed English variants weaken consistency and may violate the British English requirement.",
                issue["recommended_fix"],
                "content",
            )
        )
        content_index += 1

    for label in extract_quoted_labels(text):
        if label and label.upper() != label:
            findings.append(
                _build_finding(
                    "C",
                    content_index,
                    "Suggestion",
                    "Content Consistency",
                    f"Quoted label '{label}' is not written in ALL CAPS.",
                    "The sample project requirement expects button labels in ALL CAPS.",
                    f"Confirm whether '{label}' is a button or CTA and standardize it to '{label.upper()}'.",
                    "content",
                )
            )
            content_index += 1

    return findings


def _fallback_content_review(state: AgentState) -> list[QAFinding]:
    sources = state.get("content_sources", [])
    warning_findings = _source_warning_findings(sources)
    text = state.get("resolved_content_text", "").strip() or state.get("user_text", "")
    heuristic_findings = _fallback_text_findings(text)
    findings = [*warning_findings, *heuristic_findings]

    if findings:
        return _dedupe_findings(findings)

    return [
        _build_finding(
            "C",
            1,
            "Info",
            "Content QA",
            "No textual issues were directly inferable from the supplied request or resolved sources.",
            "A richer content sample is needed to verify grammar, terminology, subtitle quality, and storyboard copy quality.",
            "Provide a content-rich PDF, CSV, DOCX, or a pre-resolved Figma frame before rerunning content QA.",
            "content",
        )
    ]


def _normalize_llm_findings(raw_findings: list[dict], source: ContentSource) -> list[QAFinding]:
    normalized: list[QAFinding] = []
    label = _source_label(source)
    for item in raw_findings:
        evidence = str(item.get("evidence", "Model-generated content QA finding.")).strip()
        if label not in evidence:
            evidence = f"{label}: {evidence}"
        normalized.append(
            _build_finding(
                "C",
                0,
                str(item.get("severity", "Info")),
                str(item.get("area", "Content QA")),
                evidence,
                str(item.get("impact", "Potential impact on learner comprehension or content consistency.")),
                str(item.get("recommended_fix", "Review and address the issue.")),
                "content",
            )
        )
    return normalized


def _review_source_with_llm(state: AgentState, source: ContentSource, knowledge_context: str) -> list[QAFinding]:
    config = state["config"]
    api_key = config.api_key_for_provider(config.content_provider)
    chunks = _split_text_chunks(source.get("extracted_text", ""))
    if not chunks and not source.get("image_paths"):
        return []

    source_summary = summarize_content_sources([source])[0]
    location_note = ", ".join(source.get("location_hints", [])[:12]) or "No location hints available."
    warnings_note = "; ".join(source.get("warnings", [])) or "No extraction warnings."

    system_prompt = f"""
You are Content-Agent for e-learning QA.
Review the supplied source content and identify findings about:
- storyboard copy quality
- subtitles
- on-screen text
- grammar and spelling
- British English consistency
- terminology alignment
- clarity and consistency of learner-facing copy

Project knowledge:
{knowledge_context}

Return strict JSON with this shape:
{{
  "findings": [
    {{
      "severity": "Critical|Major|Minor|Suggestion|Info",
      "area": "short area",
      "evidence": "specific evidence with source/page/row/paragraph when possible",
      "impact": "impact on learner",
      "recommended_fix": "clear fix"
    }}
  ]
}}

Rules:
- Ground every finding in the supplied source content or visible image text only.
- Include source/page/row/paragraph cues whenever the evidence allows it.
- Respect British English.
- Do not drift into graphic layout review unless the issue affects text legibility or text meaning.
- If the source is sparse or partially unresolved, include an Info finding that states the missing evidence instead of pretending review coverage was complete.
""".strip()

    findings: list[QAFinding] = []
    if chunks:
        for chunk_index, chunk in enumerate(chunks, start=1):
            user_prompt = f"""Review this content QA source chunk.

Source summary:
{source_summary}

Location hints:
{location_note}

Extraction warnings:
{warnings_note}

Chunk {chunk_index}/{len(chunks)}:
{chunk}
"""
            try:
                if source.get("image_paths"):
                    raw_response = invoke_multimodal_model(
                        provider=config.content_provider,
                        model=config.content_model,
                        api_key=api_key,
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        image_paths=source.get("image_paths", []),
                    )
                else:
                    raw_response = invoke_text_model(
                        provider=config.content_provider,
                        model=config.content_model,
                        api_key=api_key,
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                    )
                payload = parse_json_object(raw_response)
                findings.extend(_normalize_llm_findings(payload.get("findings", []), source))
            except Exception:
                continue
        return findings

    user_prompt = f"""Review this content QA source.

Source summary:
{source_summary}

Location hints:
{location_note}

Extraction warnings:
{warnings_note}

There is no extracted text for this source. Review only the visible text present in the supplied image(s), and state clearly if the evidence is too limited for a complete content QA pass.
"""
    try:
        raw_response = invoke_multimodal_model(
            provider=config.content_provider,
            model=config.content_model,
            api_key=api_key,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            image_paths=source.get("image_paths", []),
        )
        payload = parse_json_object(raw_response)
        return _normalize_llm_findings(payload.get("findings", []), source)
    except Exception:
        return []


def run_content_review(state: AgentState) -> list[QAFinding]:
    config = state["config"]
    api_key = config.api_key_for_provider(config.content_provider)
    sources = state.get("content_sources", [])
    warning_findings = _source_warning_findings(sources)
    if not is_llm_enabled(config.content_provider, api_key):
        return _fallback_content_review(state)

    knowledge_context = get_knowledge_context(state["project_root"])
    llm_findings: list[QAFinding] = []
    for source in sources:
        llm_findings.extend(_review_source_with_llm(state, source, knowledge_context))

    if not llm_findings:
        resolved_text = state.get("resolved_content_text", "").strip()
        if resolved_text:
            fallback_state = dict(state)
            fallback_state["content_sources"] = []
            fallback_state["resolved_content_text"] = resolved_text
            llm_findings.extend(_fallback_content_review(fallback_state))

    combined = [*warning_findings, *llm_findings]
    if combined:
        return _dedupe_findings(combined)
    return _fallback_content_review(state)


def content_node(state: AgentState) -> AgentState:
    findings = run_content_review(state)
    log_communication(
        state["project_root"],
        "Content Agent",
        "Workflow",
        f"Produced {len(findings)} finding(s) for content review across {len(state.get('content_sources', []))} source(s).",
    )
    return {
        "messages": [],
        "findings": findings,
        "sender": "content",
        "next_agents": ["FINISH"],
        "routing_reason": state.get("routing_reason", ""),
    }
