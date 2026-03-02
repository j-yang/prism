"""Schema Generator.

Auto-generates SQL DDL from Pydantic models.
"""

from enum import Enum
from typing import Type, get_args, get_origin

from pydantic import BaseModel

from olympus.core.models import (
    BronzeVariable,
    Dependency,
    FormClassification,
    GoldStatistic,
    Param,
    PlatinumDeliverable,
    SilverVariable,
    StudyInfo,
    Visit,
)


def _python_type_to_sql(python_type: type) -> str:
    """Convert Python type to SQL type."""
    origin = get_origin(python_type)

    # Handle Optional types (Union with None)
    type_str = str(python_type)
    if "Optional" in type_str or "None" in type_str:
        args = get_args(python_type)
        if args:
            for arg in args:
                if arg is not type(None):
                    return _python_type_to_sql(arg)
        return "TEXT"

    # Handle List types
    if origin is list:
        return "JSON"

    # Handle dict types
    if origin is dict:
        return "JSON"

    # Handle Enum
    if isinstance(python_type, type) and issubclass(python_type, Enum):
        return "TEXT"

    # Basic types
    type_name = getattr(python_type, "__name__", str(python_type))

    type_mapping = {
        "str": "TEXT",
        "int": "INTEGER",
        "float": "FLOAT",
        "bool": "BOOLEAN",
        "datetime": "TIMESTAMP",
        "date": "DATE",
        "dict": "JSON",
        "Dict": "JSON",
        "list": "JSON",
        "List": "JSON",
        "Any": "TEXT",
    }

    if type_name in type_mapping:
        return type_mapping[type_name]

    # Handle string representation of types
    for key, value in type_mapping.items():
        if key in type_str:
            return value

    return "TEXT"

    # Handle Union (which Optional uses)
    if origin is type(None) | (
        hasattr(python_type, "__origin__")
        and python_type.__origin__ is type(None) | type
    ):
        pass

    # Handle List types
    if origin is list:
        return "JSON"

    # Handle dict types
    if origin is dict:
        return "JSON"

    # Basic types
    type_name = getattr(python_type, "__name__", str(python_type))

    type_mapping = {
        "str": "TEXT",
        "int": "INTEGER",
        "float": "FLOAT",
        "bool": "BOOLEAN",
        "datetime": "TIMESTAMP",
        "date": "DATE",
        "dict": "JSON",
        "Dict": "JSON",
        "list": "JSON",
        "List": "JSON",
        "Any": "TEXT",
    }

    # Handle Enum
    if isinstance(python_type, type) and issubclass(python_type, Enum):
        return "TEXT"

    # Handle string representation of types
    type_str = str(python_type)
    for key, value in type_mapping.items():
        if key in type_str:
            return value

    return "TEXT"


def pydantic_to_sql(
    model: Type[BaseModel],
    table_name: str,
    schema: str = "meta",
    primary_key: str = None,
    unique_keys: list = None,
) -> str:
    """Generate CREATE TABLE SQL from Pydantic model.

    Args:
        model: Pydantic model class
        table_name: Table name
        schema: Schema name (default: meta)
        primary_key: Primary key column name
        unique_keys: List of unique constraint column groups

    Returns:
        CREATE TABLE SQL statement
    """
    fields = []
    constraints = []

    for name, field_info in model.model_fields.items():
        python_type = field_info.annotation
        sql_type = _python_type_to_sql(python_type)

        field_def = f"    {name} {sql_type}"

        # Handle defaults
        if field_info.default is not None and not callable(field_info.default):
            if isinstance(field_info.default, bool):
                field_def += f" DEFAULT {str(field_info.default).upper()}"
            elif isinstance(field_info.default, str):
                field_def += f" DEFAULT '{field_info.default}'"
            elif isinstance(field_info.default, (int, float)):
                field_def += f" DEFAULT {field_info.default}"

        fields.append(field_def)

    # Add primary key constraint
    if primary_key:
        constraints.append(f"    PRIMARY KEY ({primary_key})")

    # Add unique constraints
    if unique_keys:
        for cols in unique_keys:
            if isinstance(cols, str):
                constraints.append(f"    UNIQUE ({cols})")
            else:
                constraints.append(f"    UNIQUE ({', '.join(cols)})")

    all_lines = fields + constraints

    return f"""CREATE TABLE IF NOT EXISTS {schema}.{table_name} (
{",\n".join(all_lines)}
);"""


def generate_meta_ddl() -> str:
    """Generate complete meta schema DDL.

    Returns:
        Complete DDL script for meta schema
    """
    tables = [
        (StudyInfo, "study_info", "studyid", None),
        (Param, "params", "paramcd", None),
        (Visit, "visits", "visit_id", None),
        (BronzeVariable, "bronze_dictionary", None, ["var_name, form_oid"]),
        (SilverVariable, "silver_dictionary", "var_name", None),
        (GoldStatistic, "gold_dictionary", None, ["element_id, group_id, schema"]),
        (PlatinumDeliverable, "platinum_dictionary", "deliverable_id", None),
        (FormClassification, "form_classification", "form_oid", None),
        (Dependency, "dependencies", None, ["from_var, to_var"]),
    ]

    parts = [
        "-- ============================================================================",
        "-- PRISM Meta Schema (Auto-generated from Pydantic Models)",
        "-- Do not edit manually - regenerate with: prism meta generate-ddl",
        "-- ============================================================================",
        "",
        "CREATE SCHEMA IF NOT EXISTS meta;",
        "",
    ]

    for model, table_name, pk, unique in tables:
        sql = pydantic_to_sql(model, table_name, "meta", pk, unique)
        parts.append(sql)
        parts.append("")

        # Add comment
        doc = model.__doc__ or f"{table_name} table"
        comment = doc.split("(")[0].strip()
        parts.append(f"COMMENT ON TABLE meta.{table_name} IS '{comment}';")
        parts.append("")

    # Add indexes
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_params_paramcd ON meta.params(paramcd);",
        "CREATE INDEX IF NOT EXISTS idx_params_category ON meta.params(category);",
        "CREATE INDEX IF NOT EXISTS idx_visits_visitnum ON meta.visits(visitnum);",
        "CREATE INDEX IF NOT EXISTS idx_bronze_dictionary_form ON meta.bronze_dictionary(form_oid);",
        "CREATE INDEX IF NOT EXISTS idx_bronze_dictionary_schema ON meta.bronze_dictionary(schema);",
        "CREATE INDEX IF NOT EXISTS idx_silver_dictionary_schema ON meta.silver_dictionary(schema);",
        "CREATE INDEX IF NOT EXISTS idx_silver_dictionary_param ON meta.silver_dictionary(param_ref);",
        "CREATE INDEX IF NOT EXISTS idx_gold_dictionary_group ON meta.gold_dictionary(group_id);",
        "CREATE INDEX IF NOT EXISTS idx_gold_dictionary_schema ON meta.gold_dictionary(schema);",
        "CREATE INDEX IF NOT EXISTS idx_gold_dictionary_deliverable ON meta.gold_dictionary(deliverable_id);",
        "CREATE INDEX IF NOT EXISTS idx_platinum_dictionary_schema ON meta.platinum_dictionary(schema);",
        "CREATE INDEX IF NOT EXISTS idx_platinum_dictionary_type ON meta.platinum_dictionary(deliverable_type);",
        "CREATE INDEX IF NOT EXISTS idx_platinum_dictionary_section ON meta.platinum_dictionary(section);",
        "CREATE INDEX IF NOT EXISTS idx_form_classification_domain ON meta.form_classification(domain);",
        "CREATE INDEX IF NOT EXISTS idx_form_classification_schema ON meta.form_classification(schema);",
        "CREATE INDEX IF NOT EXISTS idx_dependencies_from ON meta.dependencies(from_var);",
        "CREATE INDEX IF NOT EXISTS idx_dependencies_to ON meta.dependencies(to_var);",
    ]

    parts.append("-- Indexes")
    parts.extend(indexes)
    parts.append("")
    parts.append(
        "-- ============================================================================"
    )
    parts.append("-- End of Meta Schema")
    parts.append(
        "-- ============================================================================"
    )

    return "\n".join(parts)


def write_meta_ddl(path: str) -> str:
    """Write meta schema DDL to file.

    Args:
        path: Output file path

    Returns:
        Path to written file
    """
    from pathlib import Path

    ddl = generate_meta_ddl()
    Path(path).write_text(ddl, encoding="utf-8")
    return path


if __name__ == "__main__":
    print(generate_meta_ddl())
