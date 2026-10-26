import os
from services.ai_router import generate_prompt
from app.meta_client import get_comments, reply_to_comment


def build_reply(comment_text: str) -> str:
    prompt = (
        f"Write a short, warm, Facebook-style reply to this comment: '{comment_text}'. "
        "Keep it friendly, natural, and engaging, no spam."
    )
    try:
        return generate_prompt(prompt).strip()
    except Exception:
        return "Thanks for the love! More experiments coming soon."


def reply_to_post_comments(post_id: str):
    token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "")
    if not token:
        return

    comments = get_comments(post_id)
    for comment in comments:
        comment_id = comment.get("id")
        message = comment.get("message", "")
        if comment_id and message:
            reply = build_reply(message)
            reply_to_comment(comment_id, reply)
