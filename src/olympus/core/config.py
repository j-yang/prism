from pathlib import Path

PRISM_ROOT = Path(__file__).parent.parent


def get_sql_path(filename: str = "") -> Path:
    sql_dir = PRISM_ROOT / "sql"
    if filename:
        return sql_dir / filename
    return sql_dir


def get_template_path(layer: str = "", filename: str = "") -> Path:
    templates_dir = PRISM_ROOT / "agent" / "templates"
    if layer:
        templates_dir = templates_dir / layer
    if filename:
        return templates_dir / filename
    return templates_dir
