from __future__ import annotations

import io
import os
import random
from pathlib import Path

import requests
from PIL import Image, ImageOps


OUTPUT_DIR = Path("data/generated_media")
IMAGE_URL = "https://gen.pollinations.ai/image/"
IMAGE_MODEL = "black-forest-labs/flux.1-schnell"
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


