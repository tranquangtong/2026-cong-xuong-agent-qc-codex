from __future__ import annotations

import csv
import io
import shutil
import subprocess
from pathlib import Path
from typing import TypedDict


class ContrastIssue(TypedDict):
    image_path: str
    label: str
    ratio: float
    threshold: float
    foreground_hex: str
    background_hex: str
    bbox: tuple[int, int, int, int]
    large_text: bool


class ContrastAudit(TypedDict):
    issues: list[ContrastIssue]
    limitations: list[str]
    checked_images: list[str]


def _srgb_to_linear(channel: int) -> float:
    normalized = max(0.0, min(1.0, channel / 255.0))
    if normalized <= 0.04045:
        return normalized / 12.92
    return ((normalized + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb: tuple[int, int, int]) -> float:
    red, green, blue = rgb
    return (
        0.2126 * _srgb_to_linear(red)
        + 0.7152 * _srgb_to_linear(green)
        + 0.0722 * _srgb_to_linear(blue)
    )


def contrast_ratio(foreground: tuple[int, int, int], background: tuple[int, int, int]) -> float:
    foreground_luminance = relative_luminance(foreground)
    background_luminance = relative_luminance(background)
    lighter = max(foreground_luminance, background_luminance)
    darker = min(foreground_luminance, background_luminance)
    return (lighter + 0.05) / (darker + 0.05)


def _hex_color(rgb: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def _load_pillow_image():
    from PIL import Image  # type: ignore

    return Image


def _runtime_limitations() -> list[str]:
    limitations: list[str] = []
    try:
        _load_pillow_image()
    except ImportError:
        limitations.append("Pillow is not installed, so local image sampling cannot run.")

    if not shutil.which("tesseract"):
        limitations.append("The `tesseract` OCR binary is not installed, so text regions cannot be measured automatically.")
    return limitations


def _otsu_threshold(histogram: list[int]) -> int:
    total = sum(histogram)
    if total <= 0:
        return 127

    sum_total = 0
    for index, count in enumerate(histogram):
        sum_total += index * count

    sum_background = 0.0
    weight_background = 0
    max_variance = -1.0
    threshold = 127

    for index, count in enumerate(histogram):
        weight_background += count
        if weight_background == 0:
            continue

        weight_foreground = total - weight_background
        if weight_foreground == 0:
            break

        sum_background += index * count
        mean_background = sum_background / weight_background
        mean_foreground = (sum_total - sum_background) / weight_foreground
        variance_between = weight_background * weight_foreground * (mean_background - mean_foreground) ** 2

        if variance_between > max_variance:
            max_variance = variance_between
            threshold = index

    return threshold


def _mean_rgb(rgb_values: list[tuple[int, int, int]], indices: list[int]) -> tuple[int, int, int]:
    red = 0
    green = 0
    blue = 0
    for index in indices:
        sample_red, sample_green, sample_blue = rgb_values[index]
        red += sample_red
        green += sample_green
        blue += sample_blue

    count = max(1, len(indices))
    return (
        round(red / count),
        round(green / count),
        round(blue / count),
    )


def _border_values(gray_values: list[int], width: int, height: int) -> list[int]:
    if not gray_values:
        return []
    if width == 1 or height == 1:
        return list(gray_values)

    indices: list[int] = []
    for x_coord in range(width):
        indices.append(x_coord)
        indices.append((height - 1) * width + x_coord)

    for y_coord in range(1, height - 1):
        indices.append(y_coord * width)
        indices.append(y_coord * width + (width - 1))

    return [gray_values[index] for index in indices]


def _extract_ocr_words(image_path: Path) -> list[dict[str, object]]:
    command = [
        "tesseract",
        str(image_path),
        "stdout",
        "--psm",
        "11",
        "-l",
        "eng",
        "tsv",
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        error_message = result.stderr.strip() or result.stdout.strip() or "OCR failed."
        raise RuntimeError(error_message)

    words: list[dict[str, object]] = []
    reader = csv.DictReader(io.StringIO(result.stdout), delimiter="\t")
    for row in reader:
        text = str(row.get("text", "")).strip()
        if not text:
            continue
        if not any(character.isalnum() for character in text):
            continue

        try:
            confidence = float(str(row.get("conf", "-1")).strip() or "-1")
            left = int(str(row.get("left", "0")).strip() or "0")
            top = int(str(row.get("top", "0")).strip() or "0")
            width = int(str(row.get("width", "0")).strip() or "0")
            height = int(str(row.get("height", "0")).strip() or "0")
        except ValueError:
            continue

        if confidence < 55 or width <= 0 or height <= 0:
            continue

        words.append(
            {
                "text": text,
                "confidence": confidence,
                "bbox": (left, top, width, height),
            }
        )

    return words


def _analyze_word_contrast(image, bbox: tuple[int, int, int, int]) -> dict[str, object] | None:
    left, top, width, height = bbox
    if width <= 0 or height <= 0:
        return None

    pad_x = max(2, width // 4)
    pad_y = max(2, height // 3)
    crop_box = (
        max(0, left - pad_x),
        max(0, top - pad_y),
        min(image.width, left + width + pad_x),
        min(image.height, top + height + pad_y),
    )
    if crop_box[0] >= crop_box[2] or crop_box[1] >= crop_box[3]:
        return None

    crop = image.crop(crop_box).convert("RGB")
    gray_crop = crop.convert("L")
    gray_values = list(gray_crop.getdata())
    rgb_values = list(crop.getdata())
    if not gray_values or len(set(gray_values)) < 2:
        return None

    threshold = _otsu_threshold(gray_crop.histogram())
    dark_values = [value for value in gray_values if value <= threshold]
    light_values = [value for value in gray_values if value > threshold]
    if not dark_values or not light_values:
        return None

    border = _border_values(gray_values, crop.width, crop.height)
    if not border:
        return None

    border_mean = sum(border) / len(border)
    dark_mean = sum(dark_values) / len(dark_values)
    light_mean = sum(light_values) / len(light_values)
    midpoint = (dark_mean + light_mean) / 2

    background_is_dark = abs(dark_mean - border_mean) <= abs(light_mean - border_mean)
    if background_is_dark:
        background_indices = [index for index, value in enumerate(gray_values) if value < midpoint]
        text_indices = [index for index, value in enumerate(gray_values) if value >= midpoint]
    else:
        background_indices = [index for index, value in enumerate(gray_values) if value >= midpoint]
        text_indices = [index for index, value in enumerate(gray_values) if value < midpoint]

    if not background_indices or not text_indices:
        return None
    if len(text_indices) < max(12, int(len(gray_values) * 0.01)):
        return None

    foreground_rgb = _mean_rgb(rgb_values, text_indices)
    background_rgb = _mean_rgb(rgb_values, background_indices)
    return {
        "ratio": contrast_ratio(foreground_rgb, background_rgb),
        "foreground_rgb": foreground_rgb,
        "background_rgb": background_rgb,
        "large_text": height >= 24,
    }


def audit_image_contrast(image_paths: list[str], max_issues_per_image: int = 2) -> ContrastAudit:
    limitations = _runtime_limitations()
    if limitations:
        return {
            "issues": [],
            "limitations": [
                "Deterministic WCAG contrast checks were skipped: " + " ".join(limitations)
            ],
            "checked_images": [],
        }

    Image = _load_pillow_image()
    issues: list[ContrastIssue] = []
    checked_images: list[str] = []

    for raw_path in image_paths:
        image_path = Path(raw_path)
        if not image_path.exists():
            limitations.append(f"Image path does not exist for WCAG contrast checks: {image_path}")
            continue

        try:
            image = Image.open(image_path).convert("RGB")
        except Exception as exc:
            limitations.append(f"Could not open image for WCAG contrast checks: {image_path} ({exc})")
            continue

        try:
            words = _extract_ocr_words(image_path)
        except Exception as exc:
            limitations.append(f"OCR could not analyze {image_path.name} for WCAG contrast checks: {exc}")
            continue

        if not words:
            limitations.append(f"No OCR-detected text regions were found in {image_path.name}, so contrast ratio was not measured for that image.")
            continue

        checked_images.append(str(image_path))
        image_issues: list[ContrastIssue] = []
        for word in words:
            analysis = _analyze_word_contrast(image, word["bbox"])
            if not analysis:
                continue

            threshold = 3.0 if analysis["large_text"] else 4.5
            ratio = float(analysis["ratio"])
            if ratio + 0.05 >= threshold:
                continue

            image_issues.append(
                {
                    "image_path": str(image_path),
                    "label": str(word["text"]),
                    "ratio": ratio,
                    "threshold": threshold,
                    "foreground_hex": _hex_color(analysis["foreground_rgb"]),
                    "background_hex": _hex_color(analysis["background_rgb"]),
                    "bbox": word["bbox"],
                    "large_text": bool(analysis["large_text"]),
                }
            )

        image_issues.sort(key=lambda item: item["ratio"])
        issues.extend(image_issues[:max_issues_per_image])

    return {
        "issues": issues,
        "limitations": limitations,
        "checked_images": checked_images,
    }
