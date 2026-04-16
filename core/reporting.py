from __future__ import annotations

from pathlib import Path

from core.content_sources import summarize_content_sources
from core.llm import invoke_text_model, is_llm_enabled, parse_json_object
from core.state import ContentSource, QAFinding
from core.utils import ensure_text_file, make_output_bundle_dir, make_report_name, now_timestamp


def _translate_report_payload(findings: list[QAFinding], routing_reason: str, config) -> tuple[str, list[dict[str, str]]]:
    if not config:
        fallback_findings = [
            {
                "severity": finding["severity"],
                "area": finding["area"],
                "evidence": finding["evidence"],
                "impact": finding["impact"],
                "recommended_fix": finding["recommended_fix"],
            }
            for finding in findings
        ]
        return routing_reason, fallback_findings

    api_key = config.api_key_for_provider(config.content_provider)
    if not is_llm_enabled(config.content_provider, api_key):
        fallback_findings = [
            {
                "severity": finding["severity"],
                "area": finding["area"],
                "evidence": finding["evidence"],
                "impact": finding["impact"],
                "recommended_fix": finding["recommended_fix"],
            }
            for finding in findings
        ]
        return routing_reason, fallback_findings

    system_prompt = """
You translate e-learning QA reports from English to Vietnamese.
Return strict JSON with this shape:
{
  "routing_reason_vi": "translated text",
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
- Keep QA identifiers, URLs, product names, and technical acronyms unchanged where appropriate.
- Use clear professional Vietnamese.
- Preserve the meaning accurately and keep each field concise.
""".strip()
    user_prompt = str(
        {
            "routing_reason": routing_reason,
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
        }
    )

    try:
        raw = invoke_text_model(
            provider=config.content_provider,
            model=config.content_model,
            api_key=api_key,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
        payload = parse_json_object(raw)
        translated_findings = payload.get("findings_vi", [])
        if not isinstance(translated_findings, list):
            raise ValueError("Invalid translated findings payload")
        return str(payload.get("routing_reason_vi", routing_reason or "")), translated_findings
    except Exception:
        fallback_findings = [
            {
                "severity": finding["severity"],
                "area": finding["area"],
                "evidence": finding["evidence"],
                "impact": finding["impact"],
                "recommended_fix": finding["recommended_fix"],
            }
            for finding in findings
        ]
        return routing_reason, fallback_findings


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
    routing_reason_vi, translated_findings = _translate_report_payload(findings, routing_reason, config)
    source_summary = summarize_content_sources(content_sources or [])

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
    if source_summary:
        lines.extend(["", "## Tóm Tắt Nguồn"])
        lines.extend(f"- {line}" for line in source_summary)
    lines.extend(
        [
            "",
            "| ID | Mức độ | Khu vực | Nguồn | Bằng chứng | Đề xuất sửa |",
            "|---|---|---|---|---|---|",
        ]
    )

    if findings:
        for finding, translated in zip(findings, translated_findings):
            lines.append(
                "| {id} | **{severity}** | {area} | {source_agent} | {evidence} | {recommended_fix} |".format(
                    id=finding["id"],
                    severity=translated.get("severity", finding["severity"]),
                    area=translated.get("area", finding["area"]),
                    source_agent=finding["source_agent"],
                    evidence=translated.get("evidence", finding["evidence"]),
                    recommended_fix=translated.get("recommended_fix", finding["recommended_fix"]),
                )
            )
    else:
        lines.append("| N/A | **Info** | Tóm tắt QA | system | Không có findings nào được tạo ra. | Hãy rà soát lại artifact đầu vào và chạy lại nếu cần. |")

    ensure_text_file(report_path)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path
