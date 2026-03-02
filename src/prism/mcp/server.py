"""PRISM MCP Server.

Exposes PRISM capabilities as MCP tools for integration with OpenCode, Claude, etc.
"""

import sys
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("prism")


@mcp.tool()
def load_meta(meta_path: str, db_path: Optional[str] = None) -> str:
    """Load generated metadata into DuckDB meta tables.

    Args:
        meta_path: Path to generated metadata Excel file
        db_path: Path to DuckDB database (default: same name as meta file)

    Returns:
        Summary of loaded data
    """
    import pandas as pd

    from prism.core.database import Database
    from prism.meta.definitions.models import (
        MetaDefinitions,
        ParamDefinition,
        SilverVariableDefinition,
    )
    from prism.meta.loader import load_specs_to_meta
    from prism.meta.schema import generate_meta_ddl

    if not Path(meta_path).exists():
        return f"Error: Metadata file not found: {meta_path}"

    if db_path is None:
        db_path = meta_path.replace(".xlsx", ".duckdb").replace(".json", ".duckdb")

    def clean_value(val):
        if pd.isna(val):
            return None
        return val

    silver_df = pd.read_excel(meta_path, sheet_name="silver_variables")
    params_df = pd.read_excel(meta_path, sheet_name="params")

    silver_vars = []
    for _, row in silver_df.iterrows():
        var_name = clean_value(row.get("var_name"))
        if var_name:
            silver_vars.append(
                SilverVariableDefinition(
                    var_name=var_name,
                    var_label=clean_value(row.get("var_label"))
                    or clean_value(row.get("label"))
                    or "",
                    schema=clean_value(row.get("schema")) or "baseline",
                    data_type=clean_value(row.get("data_type")) or "TEXT",
                    description=clean_value(row.get("description"))
                    or clean_value(row.get("var_label"))
                    or "",
                    confidence=clean_value(row.get("confidence")) or "medium",
                    source_vars=clean_value(row.get("source_vars")),
                    transformation=clean_value(row.get("transformation"))
                    or clean_value(row.get("derivation")),
                    transformation_type=clean_value(row.get("transformation_type"))
                    or "direct",
                )
            )

    params = []
    for _, row in params_df.iterrows():
        paramcd = clean_value(row.get("paramcd"))
        if paramcd:
            params.append(
                ParamDefinition(
                    paramcd=paramcd,
                    parameter=clean_value(row.get("parameter")) or "",
                    category=clean_value(row.get("category")),
                    unit=clean_value(row.get("unit")),
                )
            )

    spec = MetaDefinitions(silver_variables=silver_vars, params=params)
    specs = [spec]

    with Database(db_path) as db:
        ddl = generate_meta_ddl()
        db.execute_script(ddl)

        summary = load_specs_to_meta(db, specs)

    result = f"Loaded to {db_path}:\n"
    result += f"  Silver variables: {summary['silver_variables']}\n"
    result += f"  Params: {summary['params']}\n"
    result += f"  Gold statistics: {summary['gold_statistics']}\n"
    result += f"  Platinum: {summary['platinum']}"

    return result


@mcp.tool()
def generate_silver(
    schema: str,
    db_path: str,
    als_path: Optional[str] = None,
    output_dir: str = "generated/silver",
) -> str:
    """Generate Silver layer Polars transformation code.

    Args:
        schema: Schema name (baseline, longitudinal, occurrence)
        db_path: Path to DuckDB database with meta tables
        als_path: Optional path to ALS Excel file for context
        output_dir: Output directory for generated Python files

    Returns:
        Summary of generated transforms
    """
    from prism.silver.agent import SilverAgent

    if not Path(db_path).exists():
        return f"Error: Database not found: {db_path}"

    agent = SilverAgent(db_path=db_path, als_path=als_path)
    transforms = agent.generate_schema_transforms(schema)

    if not transforms.transforms:
        return f"No transforms generated for {schema} schema"

    output_path = agent.save_python_file(transforms, output_dir)

    high_conf = sum(1 for t in transforms.transforms if t.confidence == "high")
    med_conf = sum(1 for t in transforms.transforms if t.confidence == "medium")
    low_conf = sum(1 for t in transforms.transforms if t.confidence == "low")

    result = f"Generated {len(transforms.transforms)} transforms for {schema}:\n"
    result += f"  High confidence: {high_conf}\n"
    result += f"  Medium confidence: {med_conf}\n"
    result += f"  Low confidence (needs review): {low_conf}\n"
    result += f"  Output: {output_path}"

    if low_conf > 0:
        result += "\n\nReview transforms marked with WARNING comments."

    return result


@mcp.tool()
def generate_gold(
    schema: str,
    db_path: str,
    output_dir: str = "generated/gold",
) -> str:
    """Generate Gold layer statistics code.

    Args:
        schema: Schema name (baseline, longitudinal, occurrence)
        db_path: Path to DuckDB database with meta tables
        output_dir: Output directory for generated Python files

    Returns:
        Summary of generated statistics
    """
    from prism.gold.agent import GoldAgent

    if not Path(db_path).exists():
        return f"Error: Database not found: {db_path}"

    agent = GoldAgent(db_path=db_path)
    transforms = agent.generate_schema_transforms(schema)

    if not transforms.transforms:
        return f"No statistics generated for {schema} schema"

    output_path = agent.save_python_file(transforms, output_dir)

    result = f"Generated {len(transforms.transforms)} statistics for {schema}:\n"
    result += f"  Output: {output_path}"

    return result


@mcp.tool()
def lookup_als_field(
    als_path: str,
    domain: Optional[str] = None,
    keywords: Optional[str] = None,
) -> str:
    """Look up ALS fields by domain and/or keywords.

    Args:
        als_path: Path to ALS Excel file
        domain: Filter by domain (e.g., DM, AE, EX)
        keywords: Comma-separated keywords to search in field labels

    Returns:
        List of matching fields
    """
    from prism.agent.base import ToolRegistry

    if not Path(als_path).exists():
        return f"Error: ALS file not found: {als_path}"

    tools = ToolRegistry(als_path=als_path)
    tools.load_als_dict(als_path)

    keyword_list = None
    if keywords:
        keyword_list = [k.strip() for k in keywords.split(",")]

    results = tools.lookup_als(domain=domain, keywords=keyword_list)

    if not results:
        return "No matching fields found"

    output = f"Found {len(results)} matching fields:\n\n"
    for field in results[:20]:
        output += f"  {field['field_oid']}\n"
        output += f"    Label: {field['label']}\n"
        output += f"    Domain: {field['domain']}\n"
        output += f"    Type: {field['data_type']}\n\n"

    if len(results) > 20:
        output += f"  ... and {len(results) - 20} more"

    return output


@mcp.tool()
def get_bronze_schema(db_path: str) -> str:
    """Get Bronze layer table schema.

    Args:
        db_path: Path to DuckDB database

    Returns:
        List of tables and columns
    """
    from prism.agent.base import ToolRegistry

    if not Path(db_path).exists():
        return f"Error: Database not found: {db_path}"

    tools = ToolRegistry(db_path=db_path)
    schema = tools.get_bronze_schema()

    if not schema:
        return "No Bronze tables found"

    output = "Bronze layer schema:\n\n"
    for table, columns in schema.items():
        output += f"  {table}:\n"
        for col in columns[:10]:
            output += f"    - {col}\n"
        if len(columns) > 10:
            output += f"    ... and {len(columns) - 10} more\n"
        output += "\n"

    return output


@mcp.tool()
def get_meta_variables(db_path: str, schema: str = "baseline") -> str:
    """Get variables from meta.silver_dictionary.

    Args:
        db_path: Path to DuckDB database
        schema: Schema name (baseline, longitudinal, occurrence)

    Returns:
        List of variables
    """
    from prism.agent.base import ToolRegistry

    if not Path(db_path).exists():
        return f"Error: Database not found: {db_path}"

    tools = ToolRegistry(db_path=db_path)
    variables = tools.get_meta_variables(schema)

    if not variables:
        return f"No variables found for {schema} schema"

    output = f"Variables in {schema} schema ({len(variables)}):\n\n"
    for var in variables[:20]:
        output += f"  {var['var_name']}\n"
        output += f"    Label: {var['var_label']}\n"
        output += f"    Type: {var['data_type']}\n"
        if var["source_vars"]:
            output += f"    Source: {var['source_vars']}\n"
        output += "\n"

    if len(variables) > 20:
        output += f"  ... and {len(variables) - 20} more"

    return output


@mcp.tool()
def list_mock_deliverables(mock_path: str) -> str:
    """List all deliverables from mock shell file.

    Args:
        mock_path: Path to mock shell file (docx/xlsx)

    Returns:
        List of deliverable IDs and titles
    """
    from prism.meta.extractor import extract_mock_shell

    if not Path(mock_path).exists():
        return f"Error: Mock shell not found: {mock_path}"

    context = extract_mock_shell(mock_path)

    if not context.deliverables:
        return "No deliverables found"

    output = f"Found {len(context.deliverables)} deliverables:\n\n"
    for d in context.deliverables:
        output += f"  {d.deliverable_id} ({d.deliverable_type})\n"
        output += f"    {d.title}\n\n"

    return output


@mcp.tool()
def extract_mock_shell(mock_path: str, output_path: Optional[str] = None) -> str:
    """Extract mock shell to JSON for inspection.

    Args:
        mock_path: Path to mock shell file (docx/xlsx)
        output_path: Optional path to save JSON (default: return as string)

    Returns:
        Extracted mock shell structure as JSON string
    """
    import json

    from prism.meta.extractor import extract_mock_shell as extract

    if not Path(mock_path).exists():
        return f"Error: Mock shell not found: {mock_path}"

    context = extract(mock_path)

    result = {
        "study_title": context.study_title,
        "protocol_no": context.protocol_no,
        "deliverables": [
            {
                "deliverable_id": d.deliverable_id,
                "deliverable_type": d.deliverable_type,
                "title": d.title,
                "population": d.population,
            }
            for d in context.deliverables
        ],
    }

    json_str = json.dumps(result, indent=2, ensure_ascii=False)

    if output_path:
        Path(output_path).write_text(json_str)
        return (
            f"Extracted to {output_path}\n\nDeliverables: {len(context.deliverables)}"
        )

    return json_str


@mcp.tool()
def list_db_deliverables(db_path: str, deliverable_type: Optional[str] = None) -> str:
    """List deliverables from meta.platinum_dictionary table.

    Args:
        db_path: Path to DuckDB database
        deliverable_type: Filter by type (table/figure/listing)

    Returns:
        List of deliverables with ID, type, title, population
    """
    import duckdb

    if not Path(db_path).exists():
        return f"Error: Database not found: {db_path}"

    try:
        con = duckdb.connect(db_path, read_only=True)

        query = (
            "SELECT deliverable_id, deliverable_type, title, population "
            "FROM meta.platinum_dictionary"
        )
        params = []

        if deliverable_type:
            query += " WHERE deliverable_type = ?"
            params.append(deliverable_type)

        query += " ORDER BY deliverable_id"

        rows = con.execute(query, params).fetchall()
        con.close()

        if not rows:
            return "No deliverables found in meta.platinum_dictionary"

        output = f"Deliverables ({len(rows)}):\n\n"
        for row in rows:
            deliv_id, deliv_type, title, population = row
            output += f"  {deliv_id} [{deliv_type}]\n"
            output += f"    {title[:60]}\n"
            if population:
                output += f"    Population: {population}\n"
            output += "\n"

        return output

    except Exception as e:
        return f"Error querying database: {e}"


@mcp.tool()
def get_variable_details(db_path: str, var_name: str) -> str:
    """Get complete definition of a variable from meta.silver_dictionary.

    Args:
        db_path: Path to DuckDB database
        var_name: Variable name to query

    Returns:
        Variable details including transformation, source vars, etc.
    """
    import duckdb

    if not Path(db_path).exists():
        return f"Error: Database not found: {db_path}"

    try:
        con = duckdb.connect(db_path, read_only=True)

        row = con.execute(
            "SELECT var_name, var_label, description, data_type, schema, "
            "source_vars, transformation, transformation_type, used_in, confidence "
            "FROM meta.silver_dictionary WHERE var_name = ?",
            [var_name],
        ).fetchone()

        con.close()

        if not row:
            return f"Variable not found: {var_name}"

        (
            var_name,
            var_label,
            description,
            data_type,
            schema,
            source_vars,
            transformation,
            transformation_type,
            used_in,
            confidence,
        ) = row

        output = f"Variable: {var_name}\n\n"
        output += f"  Label: {var_label}\n"
        output += f"  Description: {description}\n"
        output += f"  Schema: {schema}\n"
        output += f"  Data Type: {data_type}\n"
        output += f"  Confidence: {confidence}\n"

        if source_vars:
            output += f"\n  Source Variables:\n    {source_vars}\n"

        if transformation:
            output += (
                f"\n  Transformation ({transformation_type}):\n    {transformation}\n"
            )

        if used_in:
            output += f"\n  Used in Deliverables:\n    {used_in}\n"

        return output

    except Exception as e:
        return f"Error querying database: {e}"


@mcp.tool()
def list_silver_transforms() -> str:
    """List registered Silver layer transforms.

    Returns:
        List of registered transform names
    """
    from prism.transforms import list_transforms

    transforms = list_transforms()

    if not transforms:
        return "No transforms registered"

    silver_transforms = [t for t in transforms if not t.endswith("_gold")]

    if not silver_transforms:
        return "No Silver transforms registered"

    output = f"Silver transforms ({len(silver_transforms)}):\n\n"
    for name in sorted(silver_transforms):
        output += f"  - {name}\n"

    return output


@mcp.tool()
def get_transform_code(transform_name: str) -> str:
    """Get source code of a registered transform function.

    Args:
        transform_name: Name of the transform to retrieve

    Returns:
        Source code of the transform function
    """
    import inspect

    from prism.transforms import get_transform

    transform = get_transform(transform_name)

    if not transform:
        return f"Transform not found: {transform_name}"

    try:
        source = inspect.getsource(transform)
        return f"Transform: {transform_name}\n\n{source}"
    except Exception as e:
        return f"Error getting source code: {e}"


@mcp.tool()
def list_gold_transforms() -> str:
    """List registered Gold layer transforms (suffix: _gold).

    Returns:
        List of registered Gold transform names
    """
    from prism.transforms import list_transforms

    transforms = list_transforms()

    gold_transforms = [t for t in transforms if t.endswith("_gold")]

    if not gold_transforms:
        return "No Gold transforms registered"

    output = f"Gold transforms ({len(gold_transforms)}):\n\n"
    for name in sorted(gold_transforms):
        output += f"  - {name}\n"

    return output


@mcp.tool()
def generate_platinum(
    db_path: str,
    deliverable_ids: Optional[str] = None,
    deliverable_type: Optional[str] = None,
    output_path: str = "generated/platinum/report.pptx",
) -> str:
    """Generate PowerPoint slide deck from deliverables.

    Args:
        db_path: Path to DuckDB database
        deliverable_ids: Comma-separated deliverable IDs (optional)
        deliverable_type: Filter by type (table/figure/listing)
        output_path: Output PPTX file path

    Returns:
        Summary of generated slide deck
    """
    import duckdb

    from prism.platinum.agent import PlatinumAgent
    from prism.platinum.renderer import PPTXRenderer

    if not Path(db_path).exists():
        return f"Error: Database not found: {db_path}"

    try:
        con = duckdb.connect(db_path, read_only=True)

        study_info_rows = con.execute("SELECT * FROM meta.study_info").fetchall()

        study_info = {}
        if study_info_rows:
            cols = [
                desc[0]
                for desc in con.execute(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema = 'meta' AND table_name = 'study_info'"
                ).fetchall()
            ]
            row = study_info_rows[0]
            study_info = dict(zip(cols, row))

        study_info.setdefault("study_title", "Clinical Study Report")
        study_info.setdefault("protocol_no", "")

        deliverables_query = "SELECT * FROM meta.platinum_dictionary"
        params = []

        if deliverable_ids:
            deliv_ids = [d.strip() for d in deliverable_ids.split(",")]
            placeholders = ",".join("?" * len(deliv_ids))
            deliverables_query += f" WHERE deliverable_id IN ({placeholders})"
            params = deliv_ids

        if deliverable_type:
            if "WHERE" in deliverables_query:
                deliverables_query += " AND deliverable_type = ?"
            else:
                deliverables_query += " WHERE deliverable_type = ?"
            params.append(deliverable_type)

        deliverables_rows = con.execute(deliverables_query, params).fetchall()

        if not deliverables_rows:
            con.close()
            return "No deliverables found in meta.platinum_dictionary"

        cols = [
            desc[0]
            for desc in con.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = 'meta' AND table_name = 'platinum_dictionary'"
            ).fetchall()
        ]

        deliverables = [dict(zip(cols, row)) for row in deliverables_rows]
        con.close()

    except Exception as e:
        return f"Error reading database: {e}"

    agent = PlatinumAgent(db_path=db_path)

    try:
        slide_deck = agent.generate_slide_deck(study_info, deliverables)
    except Exception as e:
        return f"Error generating slides: {e}"

    try:
        renderer = PPTXRenderer()
        renderer.render_slide_deck(slide_deck)
        saved_path = renderer.save(output_path)
    except Exception as e:
        return f"Error rendering PPTX: {e}"

    result = "Generated slide deck:\n"
    result += f"  Slides: {len(slide_deck.slides)}\n"
    result += f"  Deliverables: {len(deliverables)}\n"
    result += f"  Output: {saved_path}"

    return result


@mcp.tool()
def preview_platinum_deliverable(db_path: str, deliverable_id: str) -> str:
    """Preview slide content for a single deliverable as JSON.

    Args:
        db_path: Path to DuckDB database
        deliverable_id: Deliverable ID to preview

    Returns:
        JSON representation of slide content
    """
    import duckdb

    from prism.platinum.agent import PlatinumAgent

    if not Path(db_path).exists():
        return f"Error: Database not found: {db_path}"

    try:
        con = duckdb.connect(db_path, read_only=True)

        deliverables_rows = con.execute(
            "SELECT * FROM meta.platinum_dictionary WHERE deliverable_id = ?",
            [deliverable_id],
        ).fetchall()

        if not deliverables_rows:
            con.close()
            return f"Deliverable not found: {deliverable_id}"

        cols = [
            desc[0]
            for desc in con.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = 'meta' AND table_name = 'platinum_dictionary'"
            ).fetchall()
        ]

        deliverable = dict(zip(cols, deliverables_rows[0]))
        con.close()

    except Exception as e:
        return f"Error querying database: {e}"

    agent = PlatinumAgent(db_path=db_path)

    try:
        result = agent.generate_deliverable_slides(deliverable)
        import json

        return json.dumps(result.model_dump(), indent=2, default=str)
    except Exception as e:
        return f"Error generating preview: {e}"


def main():
    """Run the MCP server."""
    print("Starting PRISM MCP Server...", file=sys.stderr)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
