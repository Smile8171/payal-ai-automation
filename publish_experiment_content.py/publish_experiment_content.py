from __future__ import annotations

import io
import json
import os
import random
import sys
from datetime import datetime, time, timedelta
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / "secrets" / ".env")
load_dotenv(ROOT / ".env")
STATE_PATH = ROOT / "data" / "publishing_state.json"
REFERENCE_DIR = ROOT / "data" / "reference_images"
GRAPH_VERSION = os.getenv("FB_GRAPH_API_VERSION", "v26.0")
GRAPH_ROOT = f"https://graph.facebook.com/{GRAPH_VERSION}"
POLLINATIONS_ROOT = "https://gen.pollinations.ai"
MEDIA_UPLOAD = "https://media.pollinations.ai/upload"
TIMEZONE = ZoneInfo(os.getenv("TIMEZONE", "Asia/Kolkata"))
IMAGE_MODEL = os.getenv("POLLINATIONS_IMAGE_MODEL", "black-forest-labs/flux.2-klein-4b")
VIDEO_MODEL = os.getenv("POLLINATIONS_VIDEO_MODEL", "google/veo-3.1-fast")
VIDEO_SECONDS = int(os.getenv("VIDEO_DURATION_SECONDS", "4"))
POST_SLOTS = (("photo_morning", time(7)), ("experiment_video", time(13)), ("photo_evening", time(19)))
OBJECTS = ("a smartphone", "a steel ball", "a glass sphere", "a synthetic diamond replica", "a citrus fruit", "a ceramic mug", "a rubber ball", "ice cubes", "a toy block", "a small watermelon")
STYLES = ("macro material study", "bright industrial documentary", "high-speed-camera look", "symmetrical product-test composition", "clean laboratory editorial", "dramatic close-up")
ACTIONS = ("slow compression", "controlled fracture", "contained deformation", "pressure test", "before-and-after test")
PHOTO_SCENES = (
    ("a village courtyard at sunrise", "in a quiet rural Indian village courtyard at sunrise, simple tasteful everyday salwar kameez, mud-plastered home, plants, and soft morning light"),
    ("a path beside village fields", "walking along a rural village path beside green fields, simple tasteful cotton salwar kameez, authentic Indian countryside, and natural daylight"),
    ("a village home in late-afternoon light", "outside a modest rural Indian village home in late-afternoon light, simple tasteful everyday Indian clothing, trees, and village homes in the background"),
)


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {"scheduled": {}, "creative_history": []}
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    if not isinstance(state, dict) or not isinstance(state.get("scheduled", {}), dict):
        raise ValueError("Publishing state must be a JSON object with a scheduled map.")
    state.setdefault("scheduled", {})
    state.setdefault("creative_history", [])
    return state


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = STATE_PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(STATE_PATH)


def request_graph(method: str, path: str, **kwargs) -> dict:
    response = requests.request(method, f"{GRAPH_ROOT}/{path.lstrip('/')}", timeout=120, **kwargs)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict) or "error" in payload:
        raise RuntimeError("Meta Graph API returned an error response.")
    return payload


def generate_text(prompt: str) -> str:
    for key_name in ("GEMINI_API_KEY", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3"):
        key = os.getenv(key_name, "").strip()
        if not key:
            continue
        try:
            response = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
                params={"key": key},
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=60,
            )
            response.raise_for_status()
            return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (requests.RequestException, KeyError, IndexError, TypeError, ValueError):
            continue
    for env_name, endpoint, model in (
        ("OPENROUTER_API_KEY", "https://openrouter.ai/api/v1/chat/completions", "openai/gpt-4o-mini"),
        ("OPENAI_API_KEY", "https://api.openai.com/v1/chat/completions", "gpt-4o-mini"),
    ):
        key = os.getenv(env_name, "").strip()
        if not key:
            continue
        try:
            response = requests.post(
                endpoint,
                headers={"Authorization": f"Bearer {key}"},
                json={"model": model, "messages": [{"role": "user", "content": prompt}]},
                timeout=60,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
        except (requests.RequestException, KeyError, IndexError, TypeError, ValueError):
            continue
    raise RuntimeError("No configured Gemini, OpenRouter, or OpenAI text provider succeeded.")


def build_plan(history: list[dict]) -> dict[str, str]:
    previous = {(item.get("object"), item.get("style"), item.get("action")) for item in history[-90:]}
    choices = [(obj, style, action) for obj in OBJECTS for style in STYLES for action in ACTIONS if (obj, style, action) not in previous]
    if not choices:
        raise RuntimeError("Experiment catalog is exhausted; add new objects, styles, or actions.")
    obj, style, action = random.choice(choices)
    return {"date": datetime.now(TIMEZONE).date().isoformat(), "object": obj, "style": style, "action": action}


def count(node: object) -> int:
    if not isinstance(node, dict):
        return 0
    summary = node.get("summary", {})
    try:
        return int(summary.get("total_count", node.get("count", 0))) if isinstance(summary, dict) else 0
    except (TypeError, ValueError):
        return 0


def video_views(post_id: str, token: str) -> int:
    try:
        data = request_graph("GET", f"{post_id}/insights", params={"access_token": token, "metric": "post_video_views"}).get("data", [])
        for metric in data if isinstance(data, list) else []:
            if isinstance(metric, dict) and metric.get("name") == "post_video_views":
                values = metric.get("values", [])
                return sum(int(item.get("value", 0)) for item in values if isinstance(item, dict)) if isinstance(values, list) else 0
    except (requests.RequestException, RuntimeError, TypeError, ValueError):
        return 0
    return 0


def engagement_theme(page_id: str, token: str) -> str:
    data = request_graph(
        "GET", f"{page_id}/posts", params={"access_token": token, "fields": "id,message,likes.summary(true),comments.summary(true),shares,attachments{media_type}", "limit": 25}
    ).get("data", [])
    candidates = [post for post in data if isinstance(post, dict) and post.get("message")] if isinstance(data, list) else []
    if not candidates:
        return "a fresh, family-friendly lifestyle photo"
    for post in candidates:
        attachments = post.get("attachments", {})
        nodes = attachments.get("data", []) if isinstance(attachments, dict) else []
        is_video = isinstance(nodes, list) and any(isinstance(node, dict) and node.get("media_type") == "video" for node in nodes)
        if is_video and isinstance(post.get("id"), str):
            post["video_views"] = video_views(post["id"], token)
    def score(post: dict) -> int:
        return count(post.get("likes")) + 2 * count(post.get("comments")) + 3 * count(post.get("shares")) + post.get("video_views", 0) // 100
    return str(max(candidates, key=score)["message"])[:500]


def upload_references(api_key: str) -> list[str]:
    if not REFERENCE_DIR.exists():
        return []
    paths = sorted(path for path in REFERENCE_DIR.iterdir() if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"})
    urls = []
    for path in paths:
        with path.open("rb") as source:
            response = requests.post(MEDIA_UPLOAD, headers={"Authorization": f"Bearer {api_key}"}, files={"file": (path.name, source)}, timeout=120)
        response.raise_for_status()
        url = response.json().get("url")
        if not isinstance(url, str) or not url.startswith("https://"):
            raise RuntimeError("Pollinations did not return a reference image URL.")
        urls.append(url)
    return urls


def generate_media(kind: str, prompt: str, model: str, api_key: str, reference: str | None = None) -> bytes:
    endpoint = "image" if kind == "photo" else "video"
    params = {"model": model, "seed": random.randint(0, 2**31 - 1)}
    if kind == "photo":
        params.update({"width": 1024, "height": 1280})
    else:
        params.update({"duration": VIDEO_SECONDS, "aspectRatio": "9:16", "audio": "false"})
    if reference and kind == "photo":
        params["image"] = reference
    response = requests.get(
        f"{POLLINATIONS_ROOT}/{endpoint}/{quote(prompt, safe='')}",
        params=params,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=300 if kind == "video" else 180,
    )
    response.raise_for_status()
    if not response.content:
        raise RuntimeError(f"Pollinations returned empty {kind} media.")
    return response.content


def schedule_photo(page_id: str, token: str, image: bytes, caption: str, publish_at: datetime) -> str:
    post = request_graph(
        "POST", f"{page_id}/photos",
        data={
            "access_token": token,
            "message": caption,
            "published": "false",
            "scheduled_publish_time": str(int(publish_at.timestamp())),
        },
        files={"source": ("lifestyle.jpg", io.BytesIO(image), "image/jpeg")},
    )
    post_id = post.get("post_id") or post.get("id")
    if not isinstance(post_id, str):
        raise RuntimeError("Meta did not return a scheduled photo post ID.")
    return post_id


def schedule_video(page_id: str, token: str, video: bytes, caption: str, publish_at: datetime) -> str:
    post = request_graph(
        "POST", f"{page_id}/videos",
        data={"access_token": token, "description": caption, "published": "false", "scheduled_publish_time": str(int(publish_at.timestamp()))},
        files={"source": ("hydraulic_experiment.mp4", io.BytesIO(video), "video/mp4")},
    )
    video_id = post.get("id")
    if not isinstance(video_id, str):
        raise RuntimeError("Meta did not return a scheduled video ID.")
    return video_id


def caption_for(plan: dict[str, str], slot: str, theme: str, is_video: bool) -> str:
    if is_video:
        prompt = (
            "Write one short, family-friendly Facebook caption in English for a simulated hydraulic-press material test. "
            "No people, injuries, dangerous instructions, unsupported claims, engagement bait, or hashtags. "
            f"Test: {plan['action']} on {plan['object']}; style: {plan['style']}; slot: {slot}. "
        )
        fallback = f"A guarded hydraulic press puts {plan['object']} through a controlled {plan['action']}. Simulated material test."
    else:
        prompt = (
            "Write one short, warm, family-friendly Facebook caption in English for a respectful everyday lifestyle photo "
            "featuring a clearly adult Indian woman. Fully clothed, non-sexualized; no engagement bait or hashtags. "
            f"Scene: {theme!r}; slot: {slot}. "
        )
        fallback = f"A little moment from {theme}. Wishing everyone a lovely day."
    try:
        return generate_text(prompt + "Return only the caption.")[:500]
    except RuntimeError:
        return fallback


def run(dry_run: bool = False) -> None:
    page_id = os.getenv("FB_PAGE_ID", "").strip()
    token = os.getenv("FB_PAGE_ACCESS_TOKEN", "").strip()
    api_key = os.getenv("POLLINATIONS_API_KEY", "").strip()
    if not dry_run and (not page_id or not token or not api_key):
        raise RuntimeError("Configure FB_PAGE_ID, FB_PAGE_ACCESS_TOKEN, and POLLINATIONS_API_KEY.")

    state = load_state()
    today = datetime.now(TIMEZONE).date()
    day_key = today.isoformat()
    scheduled = state["scheduled"]
    results = scheduled.get(day_key, {})
    missing = [name for name, _ in POST_SLOTS if name not in results]
    if not missing:
        print(f"All Payal M posts for {day_key} are already scheduled; skipping.")
        return

    history = state["creative_history"]
    plan = build_plan([item for item in history if isinstance(item, dict)])
    if dry_run:
        print(f"Dry run: plan={plan}; slots={[name for name, _ in POST_SLOTS]}; models={IMAGE_MODEL},{VIDEO_MODEL}; no API requests made.")
        return

    winning_theme = engagement_theme(page_id, token)
    brief = generate_text(
        "Write a concise visual brief for a photorealistic, family-friendly hydraulic press experiment. "
        f"Test {plan['action']} on {plan['object']}; use {plan['style']}. Use a closed safety enclosure, "
        "show only contained materials, no people or injuries. Return only the brief."
    )[:500]
    references = upload_references(api_key)
    photo_prompts = {
        name: (
            f"Photorealistic documentary-style family-friendly portrait of a fictional clearly adult 20-year-old Indian woman from a rural village, "
            f"{scene}, natural youthful adult features, calm natural expression, fully clothed in simple tasteful Indian clothing, realistic skin texture, "
            "Authentic rural Indian setting, natural light and colors; avoid elderly or middle-aged appearance, studio glamour, city scenery, or illustration. Respectful and non-sexualized; no minors, suggestive posing, text, watermark, or logo. Portrait 4:5 framing. "
            "If a reference image is provided, use only its broad visual style and composition; do not copy the person's identity or face."
        )
        for (name, _), (_, scene) in zip((POST_SLOTS[0], POST_SLOTS[1], POST_SLOTS[2]), PHOTO_SCENES)
    }
    media: dict[str, tuple[str, bytes]] = {}
    for index, name in enumerate(("photo_morning", "experiment_video", "photo_evening")):
        reference = random.choice(references) if references else None
        if name != "experiment_video":
            media[name] = ("photo", generate_media("photo", photo_prompts[name], IMAGE_MODEL, api_key, reference))
            continue
        fallback_photo = generate_media("photo", photo_prompts[name], IMAGE_MODEL, api_key, reference)
        try:
            video_prompt = (
                f"Vertical cinematic video: a guarded hydraulic press performs a slow, controlled {plan['action']} "
                f"on {plan['object']} inside a closed safety enclosure. Show the machine and contained material result. "
                "No people, injuries, dangerous activity outside the enclosure, logos, or text."
            )
            media[name] = ("video", generate_media("video", video_prompt, VIDEO_MODEL, api_key))
        except (requests.RequestException, RuntimeError) as error:
            status = getattr(getattr(error, "response", None), "status_code", None)
            suffix = f" (HTTP {status})" if status else ""
            print(f"Hydraulic video unavailable ({error.__class__.__name__}{suffix}); using the midday photo.")
            media[name] = ("photo", fallback_photo)

    for name, slot_time in POST_SLOTS:
        if name not in missing:
            continue
        publish_at = datetime.combine(today, slot_time, TIMEZONE)
        if publish_at <= datetime.now(TIMEZONE) + timedelta(minutes=15):
            publish_at += timedelta(days=1)
        media_kind, content = media[name]
        if media_kind == "video":
            caption_theme = f"{plan['action']} on {plan['object']}"
        else:
            scene_index = {"photo_morning": 0, "experiment_video": 1, "photo_evening": 2}[name]
            caption_theme = PHOTO_SCENES[scene_index][0]
        caption = caption_for(plan, name, caption_theme, media_kind == "video")
        if media_kind == "video":
            post_id = schedule_video(page_id, token, content, caption, publish_at)
        else:
            post_id = schedule_photo(page_id, token, content, caption, publish_at)
        results[name] = {"post_id": post_id, "publish_at": publish_at.isoformat()}
        scheduled[day_key] = results
        if not any(item.get("date") == plan["date"] for item in history if isinstance(item, dict)):
            history.append(plan)
            state["creative_history"] = history[-90:]
        save_state(state)
        print(f"Scheduled {name} as {media_kind} for {publish_at.isoformat()}.")


if __name__ == "__main__":
    try:
        run("--dry-run" in sys.argv[1:])
    except (OSError, ValueError, RuntimeError, requests.RequestException) as error:
        status = getattr(getattr(error, "response", None), "status_code", None)
        suffix = f" (HTTP {status})" if status else ""
        print(f"Payal M automation failed: {error.__class__.__name__}{suffix}", file=sys.stderr)
        raise SystemExit(1) from None
