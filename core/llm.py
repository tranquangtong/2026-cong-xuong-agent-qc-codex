from __future__ import annotations

import base64
import json
import mimetypes
from pathlib import Path
from typing import Any


def _is_test_key(value: str) -> bool:
    lowered = value.strip().lower()
    return not lowered or lowered.startswith("test-") or lowered.startswith("fake-")


def is_llm_enabled(provider: str, api_key: str) -> bool:
    return provider in {"groq", "google"} and not _is_test_key(api_key)


def _extract_text(response: Any) -> str:
    content = getattr(response, "content", response)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts: list[str] = []
        fallback_parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                if "text" in item:
                    text_parts.append(str(item["text"]))
                    continue
                if "thinking" in item:
                    fallback_parts.append(str(item["thinking"]))
                    continue
            fallback_parts.append(str(item))
        parts = text_parts or fallback_parts
        return "\n".join(parts)
    return str(content)


def get_chat_model(provider: str, model: str, api_key: str):
    if provider == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(model=model, api_key=api_key, temperature=0)

    if provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(model=model, google_api_key=api_key, temperature=0)

    raise ValueError(f"Unsupported provider: {provider}")


def invoke_text_model(
    *,
    provider: str,
    model: str,
    api_key: str,
    system_prompt: str,
    user_prompt: str,
) -> str:
    chat_model = get_chat_model(provider, model, api_key)
    response = chat_model.invoke([("system", system_prompt), ("human", user_prompt)])
    return _extract_text(response)


def _image_message_part(image_path: str) -> dict[str, Any] | None:
    if image_path.startswith(("http://", "https://", "data:")):
        return {
            "type": "image_url",
            "image_url": {"url": image_path},
        }

    path = Path(image_path)
    if not path.exists() or not path.is_file():
        return None

    mime_type, _ = mimetypes.guess_type(path.name)
    if not mime_type:
        mime_type = "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return {
        "type": "image_url",
        "image_url": {"url": f"data:{mime_type};base64,{encoded}"},
    }


def invoke_multimodal_model(
    *,
    provider: str,
    model: str,
    api_key: str,
    system_prompt: str,
    user_prompt: str,
    image_paths: list[str],
) -> str:
    from langchain_core.messages import HumanMessage, SystemMessage

    chat_model = get_chat_model(provider, model, api_key)
    content: list[dict[str, Any]] = [{"type": "text", "text": user_prompt}]
    for image_path in image_paths:
        image_part = _image_message_part(image_path)
        if image_part:
            content.append(image_part)
    response = chat_model.invoke([SystemMessage(content=system_prompt), HumanMessage(content=content)])
    return _extract_text(response)


def parse_json_object(raw_text: str) -> dict[str, Any]:
    text = raw_text.strip()
    if not text:
        raise ValueError("Empty model response")

    candidates = [text]
    if "```json" in text:
        for chunk in text.split("```json")[1:]:
            candidates.append(chunk.split("```", 1)[0].strip())
    if "```" in text:
        for chunk in text.split("```")[1:]:
            candidates.append(chunk.split("```", 1)[0].strip())

    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidates.append(text[first_brace : last_brace + 1])

    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue

    raise ValueError("Could not parse JSON object from model response")
