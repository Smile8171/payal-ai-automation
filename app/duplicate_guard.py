import json
from pathlib import Path

DATA_FILE = Path("data/history.json")


def load_history():
    if not DATA_FILE.exists():
        return []
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_history(history):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(history, indent=2), encoding="utf-8")


def ensure_unique(new_object, new_style):
    history = load_history()
    for item in history:
        if item.get("object") == new_object and item.get("style") == new_style:
            return False
    history.append({"object": new_object, "style": new_style})
    save_history(history)
    return True
