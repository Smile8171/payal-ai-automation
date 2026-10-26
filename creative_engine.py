import random
from datetime import datetime

OBJECTS = ["iphone", "iron ball", "glass ball", "diamond", "fruit", "steel object"]
STYLES = [
    "cinematic commercial look",
    "ultra realistic macro shot",
    "luxury product styling",
    "scientific lab experiment",
    "dramatic impact close-up",
    "high-contrast ad campaign",
]


def build_prompt_variants():
    obj = random.choice(OBJECTS)
    style = random.choice(STYLES)
    impact = random.choice([
        "sudden burst",
        "pressure impact",
        "shock test",
        "controlled fracture",
        "dramatic explosion",
    ])

    prompt = (
        f"Create a single high-quality visual of a {obj} being tested with a hydraulic machine, "
        f"showing {impact}, in a {style} aesthetic, realistic materials, sharp details, "
        "clean commercial composition, no watermark, no text, natural lighting."
    )

    return {
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "object": obj,
        "style": style,
        "impact": impact,
        "prompt": prompt,
    }
