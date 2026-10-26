from __future__ import annotations

import json
import os
import sys
from datetime import datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

from app.media_generator import generate_ai_video, generate_daily_photos


ROOT = Path(__file__).resolve().parent
STATE_PATH = ROOT / "data" / "publishing_state.json"
GRAPH_VERSION = os.getenv("FB_GRAPH_API_VERSION", "v26.0")
LOCAL_ZONE = ZoneInfo(os.getenv("TIMEZONE", "Asia/Kolkata"))
POST_SLOTS = (("photo_morning", time(7, 0)), ("photo_afternoon", time(13, 10)), ("video_evening", time(17, 0)))
GRAPH_ROOT = f"https://graph.facebook.com/{GRAPH_VERSION}"


def load_state() -> dict[str, object]:
    if not STATE_PATH.exists():
        return {"scheduled": {}}
    value = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("scheduled", {}), dict):
        raise ValueError("Publishing state must be a JSON object with a scheduled map.")
    value.setdefault("scheduled", {})
    return value


def save_state(state: dict[str, object]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = STATE_PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(STATE_PATH)


def _request(method: str, path: str, **kwargs: object) -> dict[str, object]:
    response = requests.request(method, f"{GRAPH_ROOT}/{path.lstrip('/')}", timeout=120, **kwargs)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict) or "error" in payload:
        raise RuntimeError("Meta Graph API returned an error response.")
    return payload


def engagement_theme(page_id: str, token: str) -> str:
    response = _request(
        "GET",
        f"{page_id}/posts",
        params={
            "access_token": token,
            "fields": "message,likes.summary(true),comments.summary(true),shares",
            "limit": 25,
        },
    )
    posts = response.get("data", [])
    if not isinstance(posts, list):
        return "a cheerful everyday lifestyle moment"

    def count(node: object) -> int:
        if not isinstance(node, dict):
            return 0
        summary = node.get("summary", {})
        if not isinstance(summary, dict):
            summary = {}
        try:
            return int(summary.get("total_count", node.get("count", 0)))
        except (TypeError, ValueError):
            return 0

    def score(post: object) -> int:
        if not isinstance(post, dict):
            return -1
        return (
            count(post.get("likes"))
            + 2 * count(post.get("comments"))
            + 3 * count(post.get("shares"))
        )

    candidates = [post for post in posts if isinstance(post, dict) and post.get("message")]
    if not candidates:
        return "a cheerful everyday lifestyle moment"
    top_post = max(candidates, key=score)
    return str(top_post["message"])[:500]


def generate_text(prompt: str) -> str:
    errors: list[str] = []
    gemini_keys = [
        os.getenv(name, "").strip()
        for name in ("GEMINI_API_KEY", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3")
        if os.getenv(name, "").strip()
    ]
    for index, gemini_key in enumerate(gemini_keys, start=1):
        try:
            response = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
                params={"key": gemini_key},
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=60,
            )
            response.raise_for_status()
            return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as error:
            errors.append(f"Gemini key {index}: {error.__class__.__name__}")

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
        except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as error:
            errors.append(f"{env_name}: {error.__class__.__name__}")
    raise RuntimeError("No configured text provider succeeded. " + "; ".join(errors))


def schedule_photo(page_id: str, token: str, photo: Path, caption: str, publish_at: datetime) -> str:
    with photo.open("rb") as image_file:
        uploaded = _request(
            "POST",
            f"{page_id}/photos",
            data={"access_token": token, "published": "false", "temporary": "true"},
            files={"source": (photo.name, image_file, "image/jpeg")},
        )
    photo_id = uploaded.get("id")
    if not isinstance(photo_id, str):
        raise RuntimeError("Meta did not return an uploaded photo ID.")
    result = _request(
        "POST",
        f"{page_id}/feed",
        data={
            "access_token": token,
            "message": caption,
            "attached_media[0][media_fbid]": photo_id,
            "published": "false",
            "scheduled_publish_time": str(int(publish_at.timestamp())),
        },
    )
    post_id = result.get("id")
    if not isinstance(post_id, str):
        raise RuntimeError("Meta did not return a scheduled photo post ID.")
    return post_id


def schedule_video(page_id: str, token: str, video: Path, caption: str, publish_at: datetime) -> str:
    with video.open("rb") as video_file:
        result = _request(
            "POST",
            f"{page_id}/videos",
            data={
                "access_token": token,
                "description": caption,
                "published": "false",
                "scheduled_publish_time": str(int(publish_at.timestamp())),
            },
            files={"source": (video.name, video_file, "video/mp4")},
        )
    post_id = result.get("id")
    if not isinstance(post_id, str):
        raise RuntimeError("Meta did not return a scheduled video ID.")
    return post_id


def caption_for(theme: str, slot: str) -> str:
    prompt = (
        "Write one short, warm, family-friendly Facebook Page caption in natural English. "
        "Use the successful prior-post idea only as inspiration; do not copy its wording. "
        "No misleading claims, engagement bait, hashtags, or mention of AI. "
        f"Prior high-engagement idea: {theme!r}. Content type: {slot}. Return only the caption."
    )
    return generate_text(prompt)[:500]


def run() -> None:
    page_id = os.getenv("FB_PAGE_ID", "").strip()
    token = os.getenv("FB_PAGE_ACCESS_TOKEN", "").strip()
    if not page_id or not token:
        raise RuntimeError("Configure FB_PAGE_ID and FB_PAGE_ACCESS_TOKEN as environment secrets.")

    today = datetime.now(LOCAL_ZONE).date()
    state = load_state()
    scheduled = state["scheduled"]
    assert isinstance(scheduled, dict)
    day_key = today.isoformat()
    existing_results = scheduled.get(day_key)
    if isinstance(existing_results, dict) and all(name in existing_results for name, _ in POST_SLOTS):
        print(f"Daily content for {day_key} is already scheduled; skipping.")
        return

    theme = engagement_theme(page_id, token)
    creative_brief = generate_text(
        "Create a fresh, family-friendly lifestyle theme for original AI-generated photos and video. "
        f"Use this high-performing post only as inspiration, without copying it: {theme!r}. "
        "Return one concise visual theme."
    )[:300]
    photos = generate_daily_photos(creative_brief)
    video = generate_ai_video(creative_brief, ROOT / "data" / "generated_media" / "daily_video.mp4")

    now = datetime.now(LOCAL_ZONE)
    publish_slots = [(name, datetime.combine(today, slot_time, LOCAL_ZONE)) for name, slot_time in POST_SLOTS]
    publish_slots = [
        (name, publish_at if publish_at > now + timedelta(minutes=15) else publish_at + timedelta(days=1))
        for name, publish_at in publish_slots
    ]
    results = existing_results if isinstance(existing_results, dict) else {}
    for index, (name, publish_at) in enumerate(publish_slots):
        if name in results:
            continue
        caption = caption_for(creative_brief, name)
        if name == "video_evening":
            post_id = schedule_video(page_id, token, video, caption, publish_at)
        else:
            post_id = schedule_photo(page_id, token, photos[index], caption, publish_at)
        results[name] = {"post_id": post_id, "publish_at": publish_at.isoformat()}
        scheduled[day_key] = results
        save_state(state)
        print(f"Scheduled {name} for {publish_at.isoformat()} as {post_id}.")


if __name__ == "__main__":
    try:
        run()
    except (OSError, ValueError, RuntimeError, requests.RequestException) as error:
        status = getattr(getattr(error, "response", None), "status_code", None)
        detail = f" (HTTP {status})" if status else ""
        print(f"Automation failed: {error.__class__.__name__}{detail}", file=sys.stderr)
        raise SystemExit(1) from None