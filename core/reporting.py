from __future__ import annotations

import json
from pathlib import Path

from core.content_sources import summarize_content_sources
from core.llm import invoke_text_model, is_llm_enabled, parse_json_object
from core.state import ContentSource, QAFinding
from core.utils import ensure_text_file, make_output_bundle_dir, make_report_name, now_timestamp


SEVERITY_TRANSLATIONS = {
    "Critical": "Nghiêm trọng",
    "Major": "Lớn",
    "Minor": "Nhỏ",
    "Suggestion": "Đề xuất",
    "Info": "Thông tin",
}

TRANSLATION_UNAVAILABLE_NOTE = "Không thể tạo bản dịch tiếng Việt tự động trong môi trường hiện tại."
TRANSLATION_UNAVAILABLE_FIX = "Hãy kiểm tra provider dịch hoặc API key rồi tạo lại report."


def _resolve_reporting_config(project_root: Path, config):
    if config is not None:
        return config
    try:
        from core.config import AppConfig

        return AppConfig.load(project_root)
    except Exception:
        return None


def _translation_candidates(config) -> list[tuple[str, str, str]]:
    if not config:
        return []

    ordered_pairs = [
        (config.content_provider, config.content_model),
        (config.reflection_provider, config.reflection_model),
        (config.router_provider, config.router_model),
        (config.id_provider, config.id_model),
        (config.graphic_provider, config.graphic_model),
    ]

    candidates: list[tuple[str, str, str]] = []
    seen: set[tuple[str, str]] = set()
    for provider, model in ordered_pairs:
        pair = (provider, model)
        if pair in seen:
            continue
        api_key = config.api_key_for_provider(provider)
        if not is_llm_enabled(provider, api_key):
            continue
        seen.add(pair)
        candidates.append((provider, model, api_key))
    return candidates


def _translation_unavailable_payload(findings_count: int, source_summary_count: int) -> dict[str, object]:
    return {
        "status": "unavailable",
        "routing_reason_vi": TRANSLATION_UNAVAILABLE_NOTE,
        "source_summary_vi": [TRANSLATION_UNAVAILABLE_NOTE] if source_summary_count else [],
        "findings_vi": [
            {
                "severity": "Thông tin",
                "area": "Bản dịch chưa khả dụng",
                "evidence": TRANSLATION_UNAVAILABLE_NOTE,
                "impact": TRANSLATION_UNAVAILABLE_NOTE,
                "recommended_fix": TRANSLATION_UNAVAILABLE_FIX,
            }
            for _ in range(findings_count)
        ],
    }


def _validate_translation_payload(payload: dict[str, object], findings_count: int, source_summary_count: int) -> dict[str, object]:
    routing_reason_vi = payload.get("routing_reason_vi", "")
    source_summary_vi = payload.get("source_summary_vi", [])
    findings_vi = payload.get("findings_vi", [])

    if not isinstance(routing_reason_vi, str):
        raise ValueError("Invalid routing_reason_vi payload")
    if not isinstance(source_summary_vi, list) or any(not isinstance(item, str) for item in source_summary_vi):
        raise ValueError("Invalid source_summary_vi payload")
    if not isinstance(findings_vi, list) or any(not isinstance(item, dict) for item in findings_vi):
        raise ValueError("Invalid findings_vi payload")

    if findings_count and len(findings_vi) != findings_count:
        raise ValueError("Translated findings count does not match source findings count")
    if source_summary_count and len(source_summary_vi) != source_summary_count:
        raise ValueError("Translated source summary count does not match source summary count")

    return {
        "status": "translated",
        "routing_reason_vi": routing_reason_vi,
        "source_summary_vi": source_summary_vi,
        "findings_vi": findings_vi,
    }


def _translate_report_payload(
    project_root: Path,
    findings: list[QAFinding],
    routing_reason: str,
    source_summary: list[str],
    config,
) -> dict[str, object]:
    config = _resolve_reporting_config(project_root, config)
    candidates = _translation_candidates(config)
    if not candidates:
        return _translation_unavailable_payload(len(findings), len(source_summary))

    system_prompt = """
You translate e-learning QA reports from English to Vietnamese.
Return strict JSON with this exact shape:
{
  "routing_reason_vi": "translated text",
  "source_summary_vi": ["translated source line 1"],
  "findings_vi": [
    {
      "severity": "translated severity if needed",
      "area": "translated area",
      "evidence": "translated evidence",
      "impact": "translated impact",
      "recommended_fix": "translated recommended fix"
    }
  ]
}

Rules:
- Translate every field into natural professional Vietnamese.
- Keep QA identifiers, URLs, product names, node IDs, and technical acronyms unchanged where appropriate.
- Preserve the order and count of source_summary_vi items to match source_summary exactly.
- Preserve the order and count of findings_vi items to match findings exactly.
- Do not leave full English sentences untranslated unless they are proper nouns or technical identifiers that should remain unchanged.
- Return JSON only.
""".strip()

    user_prompt = json.dumps(
        {
            "routing_reason": routing_reason,
            "source_summary": source_summary,
            "findings": [
                {
                    "severity": finding["severity"],
                    "area": finding["area"],
                    "evidence": finding["evidence"],
                    "impact": finding["impact"],
                    "recommended_fix": finding["recommended_fix"],
                }
                for finding in findings
            ],
        },
        ensure_ascii=False,
    )

    for provider, model, api_key in candidates:
        try:
            raw = invoke_text_model(
                provider=provider,
                model=model,
                api_key=api_key,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
            payload = parse_json_object(raw)
            return _validate_translation_payload(payload, len(findings), len(source_summary))
        except Exception:
            continue

    return _translation_unavailable_payload(len(findings), len(source_summary))


def generate_markdown_report(
    project_root: Path,
    findings: list[QAFinding],
    routing_reason: str = "",
    request_text: str = "",
    config=None,
    content_sources: list[ContentSource] | None = None,
) -> Path:
    output_dir = make_output_bundle_dir(project_root, request_text or "qc-run")
    report_path = output_dir / make_report_name()
    source_summary = summarize_content_sources(content_sources or [])
    translation_payload = _translate_report_payload(project_root, findings, routing_reason, source_summary, config)
    routing_reason_vi = str(translation_payload.get("routing_reason_vi", ""))
    source_summary_vi = list(translation_payload.get("source_summary_vi", []))
    translated_findings = list(translation_payload.get("findings_vi", []))

    lines = [
        "# Unified E-learning QA Report",
        f"**Generated on**: {now_timestamp()}",
    ]
    if routing_reason:
        lines.append(f"**Routing Summary**: {routing_reason}")
    if source_summary:
        lines.extend(["", "## Source Summary"])
        lines.extend(f"- {line}" for line in source_summary)
    lines.append("")
    lines.append("| ID | Severity | Area | Source | Evidence | Recommended Fix |")
    lines.append("|---|---|---|---|---|---|")

    if findings:
        for finding in findings:
            lines.append(
                "| {id} | **{severity}** | {area} | {source_agent} | {evidence} | {recommended_fix} |".format(
                    **finding
                )
            )
    else:
        lines.append("| N/A | **Info** | QA Summary | system | No findings were produced. | Review the supplied artifacts and rerun if needed. |")

    lines.extend(
        [
            "",
            "## Bản Dịch Tiếng Việt",
            f"**Thời điểm tạo**: {now_timestamp()}",
        ]
    )
    if routing_reason_vi:
        lines.append(f"**Tóm tắt điều phối**: {routing_reason_vi}")
    if translation_payload.get("status") == "unavailable":
        lines.append(f"**Ghi chú dịch**: {TRANSLATION_UNAVAILABLE_NOTE}")
    if source_summary_vi:
        lines.extend(["", "## Tóm Tắt Nguồn"])
        lines.extend(f"- {line}" for line in source_summary_vi)
    lines.extend(
        [
            "",
            "| ID | Mức độ | Khu vực | Nguồn | Bằng chứng | Đề xuất sửa |",
            "|---|---|---|---|---|---|",
        ]
    )

    if findings:
        for index, finding in enumerate(findings):
            translated = translated_findings[index] if index < len(translated_findings) else {}
            lines.append(
                "| {id} | **{severity}** | {area} | {source_agent} | {evidence} | {recommended_fix} |".format(
                    id=finding["id"],
                    severity=translated.get("severity", SEVERITY_TRANSLATIONS.get(finding["severity"], "Thông tin")),
                    area=translated.get("area", "Bản dịch chưa khả dụng"),
                    source_agent=finding["source_agent"],
                    evidence=translated.get("evidence", TRANSLATION_UNAVAILABLE_NOTE),
                    recommended_fix=translated.get("recommended_fix", TRANSLATION_UNAVAILABLE_FIX),
                )
            )
    else:
        lines.append("| N/A | **Thông tin** | Tóm tắt QA | system | Không có finding nào được tạo ra. | Hãy rà soát lại artifact đầu vào và chạy lại nếu cần. |")

    ensure_text_file(report_path)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path
