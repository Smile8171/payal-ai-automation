from __future__ import annotations

import io
import os
import random
from pathlib import Path

import requests
from PIL import Image, ImageOps


OUTPUT_DIR = Path("data/generated_media")
IMAGE_URL = "https://gen.pollinations.ai/image/"
VIDEO_URL = "https://gen.pollinations.ai/video/"
IMAGE_MODEL = "black-forest-labs/flux.1-schnell"
VIDEO_MODEL = os.getenv("POLLINATIONS_VIDEO_MODEL", "google/gemini-omni-1.1-flash")
VIDEO_DURATION = int(os.getenv("POLLINATIONS_VIDEO_DURATION", "5"))
IMAGE_SIZE = (1024, 1280)


def _pollinations_key() -> str:
    key = os.getenv("POLLINATIONS_API_KEY", "").strip()
    if not key:
        raise RuntimeError("Configure POLLINATIONS_API_KEY before generating images.")
    return key


def generate_photo(prompt: str, output_path: Path, seed: int) -> Path:
    response = requests.get(
        IMAGE_URL + requests.utils.quote(prompt, safe=""),
        params={
            "model": IMAGE_MODEL,
            "width": IMAGE_SIZE[0],
            "height": IMAGE_SIZE[1],
            "seed": seed,
            "nologo": "true",
        },
        headers={"Authorization": f"Bearer {_pollinations_key()}"},
        timeout=180,
    )
    response.raise_for_status()

    with Image.open(io.BytesIO(response.content)) as generated:
        image = ImageOps.exif_transpose(generated).convert("RGB")
        image = ImageOps.fit(image, IMAGE_SIZE, method=Image.Resampling.LANCZOS)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="JPEG", quality=90, optimize=True)
    return output_path


def generate_daily_photos(theme: str) -> list[Path]:
    prompts = (
        f"Photorealistic family-friendly lifestyle editorial, portrait of a fictional adult woman age 25 or older, {theme}, natural confident pose, tasteful contemporary clothing, bright window light, realistic skin texture, 4:5 vertical framing, no text, no watermark, no logo.",
        f"A distinct photorealistic family-friendly fashion editorial featuring a different pose and camera angle for a fictional adult woman age 25 or older, {theme}, tasteful modern outfit, outdoor garden background, soft daylight, 4:5 vertical framing, no text, no watermark, no logo.",
    )
    return [
        generate_photo(
            prompt,
            OUTPUT_DIR / f"photo_{index + 1}.jpg",
            random.randint(0, 2**31 - 1),
        )
        for index, prompt in enumerate(prompts)
    ]


def generate_ai_video(theme: str, output_path: Path) -> Path:
    if not 3 <= VIDEO_DURATION <= 10:
        raise ValueError("POLLINATIONS_VIDEO_DURATION must be between 3 and 10 seconds.")

    prompt = (
        "Create an original, polished, photorealistic short video for a family-friendly Facebook Page. "
        "Portrait 9:16 composition, a single continuous cinematic shot, gentle natural camera motion. "
        "Feature one fictional adult woman age 25 or older in tasteful contemporary clothing, with a "
        "warm confident expression and natural movement. Visual theme: "
        f"{theme}. Use realistic lighting and a clean lifestyle-editorial look. "
        "No text, captions, logos, watermarks, extra people, or dialogue."
    )
    response = requests.get(
        VIDEO_URL + requests.utils.quote(prompt, safe=""),
        params={
            "model": VIDEO_MODEL,
            "duration": VIDEO_DURATION,
            "resolution": "720p",
            "aspect_ratio": "9:16",
        },
        headers={"Authorization": f"Bearer {_pollinations_key()}"},
        timeout=300,
    )
    response.raise_for_status()
    content = response.content
    if len(content) < 12 or content[4:8] != b"ftyp":
        raise RuntimeError("Pollinations did not return a valid MP4 video.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary_path.write_bytes(content)
    temporary_path.replace(output_path)
    return output_path