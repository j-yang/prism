from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent


def get_template_path(layer: str, filename: str) -> Path:
    return TEMPLATES_DIR / layer / filename
