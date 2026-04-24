from __future__ import annotations

import base64
import json
import mimetypes
from pathlib import Path
from typing import Any

import httpx


def _is_test_key(value: str) -> bool:
    lowered = value.strip().lower()
    return not lowered or lowered.startswith("test-") or lowered.startswith("fake-")


def is_llm_enabled(provider: str, api_key: str) -> bool:
    return provider in {"groq", "google", "openai"} and not _is_test_key(api_key)


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


def _extract_openai_compatible_text(payload: dict[str, Any]) -> str:
    choices = payload.get("choices", [])
    if not choices:
        raise ValueError("No choices returned by provider")
    message = choices[0].get("message", {})
    return _extract_text(message.get("content", ""))


def _extract_gemini_text(payload: dict[str, Any]) -> str:
    candidates = payload.get("candidates", [])
    if not candidates:
        raise ValueError("No candidates returned by Gemini")
    parts = candidates[0].get("content", {}).get("parts", [])
    texts = [str(part.get("text", "")) for part in parts if isinstance(part, dict) and part.get("text")]
    if texts:
        return "\n".join(texts)
    raise ValueError("Gemini response did not contain text parts")


def get_chat_model(provider: str, model: str, api_key: str):
    if provider == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(model=model, api_key=api_key, temperature=0)

    if provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(model=model, google_api_key=api_key, temperature=0)

    raise ValueError(f"Unsupported provider: {provider}")


def _invoke_groq_http(*, model: str, api_key: str, messages: list[dict[str, Any]]) -> str:
    response = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "temperature": 0,
            "messages": messages,
        },
        timeout=120,
    )
    response.raise_for_status()
    return _extract_openai_compatible_text(response.json())


def _data_url_to_gemini_part(image_url: str) -> dict[str, Any] | None:
    if not image_url.startswith("data:") or ";base64," not in image_url:
        return None
    header, encoded = image_url.split(",", 1)
    mime_type = header[5:].split(";")[0] or "image/png"
    return {
        "inline_data": {
            "mime_type": mime_type,
            "data": encoded,
        }
    }


def _invoke_google_http(*, model: str, api_key: str, system_prompt: str, user_content: list[dict[str, Any]]) -> str:
    parts: list[dict[str, Any]] = []
    for item in user_content:
        item_type = item.get("type")
        if item_type == "text":
            parts.append({"text": str(item.get("text", ""))})
            continue
        if item_type == "image_url":
            image_url = item.get("image_url", {}).get("url", "")
            gemini_part = _data_url_to_gemini_part(str(image_url))
            if gemini_part:
                parts.append(gemini_part)

    response = httpx.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        params={"key": api_key},
        headers={"Content-Type": "application/json"},
        json={
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {"temperature": 0},
        },
        timeout=120,
    )
    response.raise_for_status()
    return _extract_gemini_text(response.json())


def _invoke_http_model(
    *,
    provider: str,
    model: str,
    api_key: str,
    system_prompt: str,
    user_content: list[dict[str, Any]],
) -> str:
    if provider == "groq":
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content if len(user_content) > 1 or user_content[0]["type"] != "text" else user_content[0]["text"]},
        ]
        return _invoke_groq_http(model=model, api_key=api_key, messages=messages)
    if provider == "google":
        return _invoke_google_http(model=model, api_key=api_key, system_prompt=system_prompt, user_content=user_content)
    raise ValueError(f"Unsupported provider: {provider}")


def invoke_text_model(
    *,
    provider: str,
    model: str,
    api_key: str,
    system_prompt: str,
    user_prompt: str,
) -> str:
    try:
        chat_model = get_chat_model(provider, model, api_key)
        response = chat_model.invoke([("system", system_prompt), ("human", user_prompt)])
        return _extract_text(response)
    except ModuleNotFoundError:
        return _invoke_http_model(
            provider=provider,
            model=model,
            api_key=api_key,
            system_prompt=system_prompt,
            user_content=[{"type": "text", "text": user_prompt}],
        )


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
    content: list[dict[str, Any]] = [{"type": "text", "text": user_prompt}]
    for image_path in image_paths:
        image_part = _image_message_part(image_path)
        if image_part:
            content.append(image_part)
    try:
        from langchain_core.messages import HumanMessage, SystemMessage

        chat_model = get_chat_model(provider, model, api_key)
        response = chat_model.invoke([SystemMessage(content=system_prompt), HumanMessage(content=content)])
        return _extract_text(response)
    except ModuleNotFoundError:
        return _invoke_http_model(
            provider=provider,
            model=model,
            api_key=api_key,
            system_prompt=system_prompt,
            user_content=content,
        )


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


def invoke_openai_transcription(
    *,
    model: str,
    api_key: str,
    audio_path: str,
) -> dict[str, Any]:
    with Path(audio_path).open("rb") as handle:
        response = httpx.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {api_key}"},
            data={
                "model": model,
                "response_format": "verbose_json",
                "timestamp_granularities[]": "segment",
            },
            files={"file": (Path(audio_path).name, handle, "audio/wav")},
            timeout=300,
        )
    response.raise_for_status()
    payload = response.json()
    return payload if isinstance(payload, dict) else {}
