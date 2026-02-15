from pathlib import Path

SQL_DIR = Path(__file__).parent


def get_init_meta_sql() -> str:
    return (SQL_DIR / "init_meta.sql").read_text(encoding="utf-8")


def get_init_gold_sql() -> str:
    return (SQL_DIR / "init_gold.sql").read_text(encoding="utf-8")


def get_init_traceability_sql() -> str:
    return (SQL_DIR / "init_traceability.sql").read_text(encoding="utf-8")
