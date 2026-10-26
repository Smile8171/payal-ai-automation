import random
from app.creative_engine import build_prompt_variants
from app.duplicate_guard import ensure_unique
from services.ai_router import generate_prompt


def generate_daily_plan():
    plan = build_prompt_variants()

    while True:
        if ensure_unique(plan["object"], plan["style"]):
            break
        plan = build_prompt_variants()

    ai_text = generate_prompt(plan["prompt"])
    caption = (
        f"Daily impact experiment: {plan['object']} in {plan['style']} "
        f"with {plan['impact']}. AI-generated test #{random.randint(100, 999)}"
    )

    return {"plan": plan, "ai_text": ai_text, "caption": caption}
