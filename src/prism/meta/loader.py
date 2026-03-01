"""Spec Loader.

Load generated meta definitions into meta tables.
"""

from typing import List

from prism.core.database import Database
from prism.meta.definitions.models import MetaDefinitions


def load_spec_to_meta(
    db: Database, spec: MetaDefinitions, study_id: str = None
) -> dict:
    """Load meta definitions into meta tables.

    Args:
        db: Database connection
        spec: Meta definitions
        study_id: Optional study identifier

    Returns:
        Summary of loaded items
    """
    summary = {
        "silver_variables": 0,
        "params": 0,
        "gold_statistics": 0,
        "platinum": 0,
        "errors": [],
    }

    # Load silver variables
    for var in spec.silver_variables:
        try:
            db.execute(
                """
                INSERT INTO meta.silver_dictionary 
                (var_name, var_label, schema, data_type, source_vars, 
                 transformation, transformation_type, param_ref, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (var_name) DO UPDATE SET
                    var_label = EXCLUDED.var_label,
                    schema = EXCLUDED.schema,
                    data_type = EXCLUDED.data_type,
                    source_vars = EXCLUDED.source_vars,
                    transformation = EXCLUDED.transformation,
                    transformation_type = EXCLUDED.transformation_type,
                    param_ref = EXCLUDED.param_ref,
                    description = EXCLUDED.description
                """,
                [
                    var.var_name,
                    var.var_label,
                    var.schema,
                    var.data_type,
                    var.source_vars,
                    var.transformation,
                    var.transformation_type,
                    var.param_ref,
                    var.description,
                ],
            )
            summary["silver_variables"] += 1
        except Exception as e:
            summary["errors"].append(f"silver.{var.var_name}: {e}")

    # Load params
    for param in spec.params:
        try:
            db.execute(
                """
                INSERT INTO meta.params 
                (paramcd, parameter, category, unit, 
                 default_source_form, default_source_var)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT (paramcd) DO UPDATE SET
                    parameter = EXCLUDED.parameter,
                    category = EXCLUDED.category,
                    unit = EXCLUDED.unit,
                    default_source_form = EXCLUDED.default_source_form,
                    default_source_var = EXCLUDED.default_source_var
                """,
                [
                    param.paramcd,
                    param.parameter,
                    param.category,
                    param.unit,
                    param.default_source_form,
                    param.default_source_var,
                ],
            )
            summary["params"] += 1
        except Exception as e:
            summary["errors"].append(f"param.{param.paramcd}: {e}")

    # Load gold statistics
    for stat in spec.gold_statistics:
        try:
            import json

            statistics_json = json.dumps(stat.statistics) if stat.statistics else None
            db.execute(
                """
                INSERT INTO meta.gold_dictionary 
                (element_id, group_id, schema, population, selection, 
                 statistics, deliverable_id, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    stat.element_id,
                    stat.group_id,
                    stat.schema,
                    stat.population,
                    stat.selection,
                    statistics_json,
                    stat.deliverable_id,
                    stat.description,
                ],
            )
            summary["gold_statistics"] += 1
        except Exception as e:
            summary["errors"].append(f"gold.{stat.element_id}: {e}")

    # Load platinum deliverables
    for platinum in spec.platinum:
        try:
            import json

            elements_json = json.dumps(platinum.elements) if platinum.elements else None
            db.execute(
                """
                INSERT INTO meta.platinum_dictionary 
                (deliverable_id, deliverable_type, title, schema, population, elements)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT (deliverable_id) DO UPDATE SET
                    deliverable_type = EXCLUDED.deliverable_type,
                    title = EXCLUDED.title,
                    schema = EXCLUDED.schema,
                    population = EXCLUDED.population,
                    elements = EXCLUDED.elements
                """,
                [
                    platinum.deliverable_id,
                    platinum.deliverable_type,
                    platinum.title,
                    platinum.schema,
                    platinum.population,
                    elements_json,
                ],
            )
            summary["platinum"] += 1
        except Exception as e:
            summary["errors"].append(f"platinum.{platinum.deliverable_id}: {e}")

    return summary


def load_specs_to_meta(db: Database, specs: List[MetaDefinitions]) -> dict:
    """Load multiple meta definitions into meta tables.

    Args:
        db: Database connection
        specs: List of meta definitions

    Returns:
        Combined summary
    """
    combined = {
        "silver_variables": 0,
        "params": 0,
        "gold_statistics": 0,
        "platinum": 0,
        "errors": [],
    }

    for spec in specs:
        summary = load_spec_to_meta(db, spec)
        combined["silver_variables"] += summary["silver_variables"]
        combined["params"] += summary["params"]
        combined["gold_statistics"] += summary["gold_statistics"]
        combined["platinum"] += summary["platinum"]
        combined["errors"].extend(summary["errors"])

    return combined
