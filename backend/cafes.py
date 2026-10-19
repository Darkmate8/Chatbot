from pathlib import Path

CAFES_DIR = Path(__file__).resolve().parent.parent / "cafes"
CAFES = {
    "hashtag": "Hashtag",
    "coffee_nation": "Coffee Nation",
    "juice_press": "Juice Press",
    "barsha": "Barsha",
}
NO_INFO = "No info yet. Do not describe this cafe's menu, layout or features."


def load_all_cafe_contexts(cafes_dir=CAFES_DIR):
    sections = []
    for slug, name in CAFES.items():
        path = Path(cafes_dir) / f"{slug}.md"
        body = path.read_text() if path.exists() else NO_INFO
        sections.append(f"## {name} ({slug})\n{body}")
    return "\n\n".join(sections)
