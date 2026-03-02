"""PydanticAI agent for Silver transformation generation.

Generates Polars Python code for Silver layer transformations.
"""

import json
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field

from olympus.agent.base import BaseAgent


class GeneratedTransform(BaseModel):
    """Generated Polars transformation for a single variable."""

    var_name: str = Field(..., description="Variable name (snake_case)")
    var_label: str = Field(..., description="Human readable label")
    code: str = Field(..., description="Complete Python function code")
    source_vars: List[str] = Field(
        default_factory=list, description="Source variables needed"
    )
    dependencies: List[str] = Field(
        default_factory=list, description="Other derived variables needed"
    )
    confidence: str = Field(
        default="medium", description="Generation confidence (high/medium/low)"
    )
    notes: Optional[str] = Field(default=None, description="Notes for reviewer")


class SchemaTransforms(BaseModel):
    """All transforms for a schema."""

    schema_name: str = Field(
        ..., description="Schema name (baseline/longitudinal/occurrence)"
    )
    imports: str = Field(
        default="import polars as pl\nfrom datetime import datetime",
        description="Required imports",
    )
    transforms: List[GeneratedTransform] = Field(default_factory=list)


SYSTEM_PROMPT_SILVER = """You are a clinical trial data transformation expert.

Generate Polars Python code for Silver layer transformations.
You have access to tools to look up ALS fields, check dependencies, and get existing variables.

CRITICAL REQUIREMENTS:
1. Output ONLY valid Python code
2. Use Polars (pl) syntax, NOT Pandas
3. Each transform must be a Complete function
4. Handle edge cases (nulls, type conversions)
5. Follow clinical data standards

POLARS PATTERNS:
- Conditional: `pl.when(condition).then(value).otherwise(default)`
- String contains: `pl.col("col").str.contains("pattern")`
- Is in list: `pl.col("col").is_in(["A", "B"])`
- Date diff: `(pl.col("end") - pl.col("start")).dt.total_days()`
- Type cast: `pl.col("col").cast(pl.Int64)`
- Coalesce: `pl.coalesce([pl.col("a"), pl.col("b")])`
- Fill null: `pl.col("col").fill_null(value)`

OUTPUT FORMAT:
Return JSON matching SchemaTransforms schema exactly.
"""


class SilverAgent(BaseAgent):
    """PydanticAI agent for generating Silver transformations."""

    def __init__(
        self,
        provider: str = "deepseek",
        db_path: Optional[str] = None,
        als_path: Optional[str] = None,
    ):
        super().__init__(provider=provider, db_path=db_path, als_path=als_path)

    def _get_system_prompt(self) -> str:
        return SYSTEM_PROMPT_SILVER

    def generate_schema_transforms(
        self,
        schema: str,
        variables: Optional[List[dict]] = None,
    ) -> SchemaTransforms:
        """Generate all transforms for a schema.

        Args:
            schema: Schema name (baseline, longitudinal, occurrence)
            variables: List of variable dicts from meta.silver_dictionary.
                       If None, will fetch from database.

        Returns:
            SchemaTransforms with all generated code
        """
        if variables is None:
            variables = self.tools.get_meta_variables(schema, self.db_path)

        if not variables:
            print(f"No variables found for {schema} schema")
            return SchemaTransforms(schema_name=schema)

        derived_vars = [
            v
            for v in variables
            if v.get("transformation_type") == "python" or v.get("transformation")
        ]

        if not derived_vars:
            print(f"No derived variables found for {schema} schema")
            return SchemaTransforms(schema_name=schema)

        als_fields = self.tools.lookup_als()
        als_json = json.dumps(als_fields[:50], indent=2, ensure_ascii=False)[:3000]

        vars_json = json.dumps(derived_vars, indent=2, ensure_ascii=False)[:6000]

        prompt = f"""## Task: Generate Silver Transforms for {schema} Schema

### Variables to Derive
```json
{vars_json}
```

### Available ALS Fields
```json
{als_json}
```

---

## Output Schema

Return JSON matching this structure:
```json
{{
  "schema_name": "{schema}",
  "imports": "import polars as pl\\nfrom datetime import datetime",
  "transforms": [
    {{
      "var_name": "teae_flg",
      "var_label": "Treatment Emergent AE Flag",
      "code": "def derive_teae_flg(df: pl.DataFrame) -> pl.DataFrame:\\n    return df.with_columns([\\n        pl.when(pl.col('ae_start_date') >= pl.col('first_dose_date'))\\n          .then(pl.lit('Y'))\\n          .otherwise(pl.lit('N'))\\n          .alias('teae_flg')\\n    ])",
      "source_vars": ["ae_start_date", "first_dose_date"],
      "dependencies": [],
      "confidence": "high",
      "notes": null
    }}
  ]
}}
```

---

## Rules

1. **var_name**: Must match the variable name from input
2. **code**: Complete Python function with:
   - Function name: `derive_{{var_name}}`
   - Takes `df: pl.DataFrame` as input
   - Returns `pl.DataFrame` with new column added
   - Use `.with_columns()` pattern
3. **source_vars**: List of columns read from input DataFrame
4. **dependencies**: List of other derived variables this depends on
5. **confidence**:
   - "high" = straightforward transformation
   - "medium" = reasonable assumptions made
   - "low" = uncertain, needs review

Generate transforms for ALL variables in the input list.
"""

        return self.run(prompt, result_type=SchemaTransforms)

    def generate_python_file(self, transforms: SchemaTransforms) -> str:
        """Generate complete Python file content.

        Args:
            transforms: SchemaTransforms from generation

        Returns:
            Complete Python file content
        """
        lines = [
            f'"""Silver transformations for {transforms.schema_name} schema.',
            "",
            "Auto-generated by PRISM Silver Agent.",
            "Review and modify as needed before execution.",
            '"""',
            "",
            transforms.imports,
            "from olympus.transforms.registry import register_transform",
            "",
            "",
        ]

        for t in transforms.transforms:
            lines.append(f"# {t.var_label}")
            if t.notes:
                lines.append(f"# NOTE: {t.notes}")
            if t.confidence == "low":
                lines.append("# WARNING: Low confidence - needs review")

            lines.append(f'@register_transform("{t.var_name}")')
            lines.append(t.code)
            lines.append("")
            lines.append("")

        return "\n".join(lines)

    def save_python_file(
        self,
        transforms: SchemaTransforms,
        output_dir: str = "generated/silver",
    ) -> str:
        """Save generated transforms to Python file.

        Args:
            transforms: SchemaTransforms from generation
            output_dir: Output directory

        Returns:
            Path to saved file
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        file_path = output_path / f"{transforms.schema_name}.py"
        content = self.generate_python_file(transforms)
        file_path.write_text(content, encoding="utf-8")

        print(f"Generated {len(transforms.transforms)} transforms")
        print(f"Output: {file_path}")

        return str(file_path)
