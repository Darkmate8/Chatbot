from pathlib import Path

CAFES_DIR = Path(__file__).resolve().parent.parent / "cafes"
CAFES_WITH_CONTEXT = {"hashtag", "coffee_nation", "juice_press", "barsha"}


def load_cafe_context(cafe):
    if cafe not in CAFES_WITH_CONTEXT:
        raise ValueError(f"Unknown cafe: {cafe!r}. Expected one of {sorted(CAFES_WITH_CONTEXT)}")
    return (CAFES_DIR / f"{cafe}.md").read_text()
