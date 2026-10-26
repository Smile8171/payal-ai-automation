from services.gemini_service import generate_text as gemini_generate
from services.openrouter_service import generate_text as openrouter_generate
from services.openai_service import generate_text as openai_generate


def generate_prompt(prompt: str):
    for name, fn in [
        ("gemini", gemini_generate),
        ("openrouter", openrouter_generate),
        ("openai", openai_generate),
    ]:
        try:
            return fn(prompt)
        except Exception as exc:
            print(f"{name} failed: {exc}")
    raise RuntimeError("All AI providers failed")
