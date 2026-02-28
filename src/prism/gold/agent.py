"""PydanticAI agent for Gold transformation generation.

Generates Polars Python code for Gold layer statistical aggregations.
"""

import json
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field

from prism.agent.base import BaseAgent


class GeneratedGoldTransform(BaseModel):
    """Generated Gold transformation for a single statistic."""

    deliverable_id: str = Field(..., description="Deliverable ID (e.g., 14.1.1)")
    row_label: str = Field(..., description="Row label in table")
    element_type: str = Field(..., description="Element type (variable/param/flag)")
    element_id: str = Field(..., description="Variable name or paramcd")
    code: str = Field(..., description="Complete Python function code")
    group_by: List[str] = Field(
        default_factory=lambda: ["treatment_group"],
        description="Grouping columns",
    )
    statistics: List[str] = Field(
        default_factory=lambda: ["n", "mean", "sd"],
        description="Statistics to compute",
    )
    selection: Optional[str] = Field(
        default=None, description="Filter condition (e.g., SAFFL = 'Y')"
    )
    confidence: str = Field(
        default="medium", description="Generation confidence (high/medium/low)"
    )
    notes: Optional[str] = Field(default=None, description="Notes for reviewer")


class SchemaGoldTransforms(BaseModel):
    """All Gold transforms for a schema."""

    schema_name: str = Field(
        ..., description="Schema name (baseline/longitudinal/occurrence)"
    )
    imports: str = Field(
        default="import polars as pl\nfrom typing import Dict, Any",
        description="Required imports",
    )
    transforms: List[GeneratedGoldTransform] = Field(default_factory=list)


SYSTEM_PROMPT_GOLD = """You are a clinical trial statistics expert.

Generate Polars Python code for Gold layer statistical aggregations.
You understand clinical trial statistics: n, mean, sd, median, min, max, etc.

CRITICAL REQUIREMENTS:
1. Output ONLY valid Python code
2. Use Polars (pl) syntax, NOT Pandas
3. Each transform must be a complete function
4. Follow clinical trial reporting standards

POLARS AGGREGATION PATTERNS:
- Count: `pl.len()`
- Mean: `pl.col("col").mean()`
- Std dev: `pl.col("col").std()`
- Median: `pl.col("col").median()`
- Min/Max: `pl.col("col").min()`, `pl.col("col").max()`
- Sum: `pl.col("col").sum()`
- Unique count: `pl.col("col").n_unique()`

GROUP BY PATTERN:
```python
result = df.group_by(["treatment_group"]).agg([
    pl.len().alias("n"),
    pl.col("value").mean().alias("mean"),
    pl.col("value").std().alias("sd"),
])
```

OUTPUT FORMAT:
Return JSON matching SchemaGoldTransforms schema exactly.
"""


class GoldAgent(BaseAgent):
    """PydanticAI agent for generating Gold transformations."""

    def __init__(
        self,
        provider: str = "deepseek",
        db_path: Optional[str] = None,
        als_path: Optional[str] = None,
    ):
        super().__init__(provider=provider, db_path=db_path, als_path=als_path)

    def _get_system_prompt(self) -> str:
        return SYSTEM_PROMPT_GOLD

    def generate_schema_transforms(
        self,
        schema: str,
        variables: Optional[List[dict]] = None,
        deliverables: Optional[List[str]] = None,
    ) -> SchemaGoldTransforms:
        """Generate all Gold transforms for a schema.

        Args:
            schema: Schema name (baseline, longitudinal, occurrence)
            variables: List of variable dicts from meta.silver_dictionary.
                       If None, will fetch from database.
            deliverables: Optional list of deliverable IDs to filter

        Returns:
            SchemaGoldTransforms with all generated code
        """
        if variables is None:
            variables = self.tools.get_meta_variables(schema, self.db_path)

        if not variables:
            print(f"No variables found for {schema} schema")
            return SchemaGoldTransforms(schema_name=schema)

        vars_json = json.dumps(variables, indent=2, ensure_ascii=False)[:6000]

        prompt = f"""## Task: Generate Gold Transforms for {schema} Schema

### Silver Variables Available
```json
{vars_json}
```

---

## Output Schema

Return JSON matching this structure:
```json
{{
  "schema_name": "{schema}",
  "imports": "import polars as pl\\nfrom typing import Dict, Any",
  "transforms": [
    {{
      "deliverable_id": "14.1.1",
      "row_label": "Age (years)",
      "element_type": "variable",
      "element_id": "age",
      "code": "def compute_age_stats(df: pl.DataFrame) -> pl.DataFrame:\\n    return df.group_by(['treatment_group']).agg([\\n        pl.len().alias('n'),\\n        pl.col('age').mean().alias('mean'),\\n        pl.col('age').std().alias('sd'),\\n        pl.col('age').median().alias('median'),\\n        pl.col('age').min().alias('min'),\\n        pl.col('age').max().alias('max'),\\n    ])",
      "group_by": ["treatment_group"],
      "statistics": ["n", "mean", "sd", "median", "min", "max"],
      "selection": null,
      "confidence": "high",
      "notes": null
    }}
  ]
}}
```

---

## Rules

1. **deliverable_id**: Identify which deliverable this statistic belongs to
2. **row_label**: Human-readable label for the table row
3. **element_type**: 
   - "variable" = regular column
   - "param" = longitudinal parameter
   - "flag" = yes/no flag
4. **element_id**: Variable name or paramcd
5. **code**: Complete Python function with:
   - Function name: `compute_{{element_id}}_stats`
   - Takes `df: pl.DataFrame` as input
   - Returns `pl.DataFrame` with aggregated statistics
   - Use `.group_by().agg()` pattern
6. **statistics**: List of statistics computed (n, mean, sd, median, min, max, etc.)
7. **confidence**:
   - "high" = standard statistics
   - "medium" = reasonable assumptions
   - "low" = uncertain, needs review

Generate transforms for appropriate variables from the input list.
Focus on continuous variables (age, lab values, scores) and categorical variables (sex, race).
"""

        return self.run(prompt, result_type=SchemaGoldTransforms)

    def generate_python_file(self, transforms: SchemaGoldTransforms) -> str:
        """Generate complete Python file content.

        Args:
            transforms: SchemaGoldTransforms from generation

        Returns:
            Complete Python file content
        """
        lines = [
            f'"""Gold transformations for {transforms.schema_name} schema.',
            "",
            "Auto-generated by PRISM Gold Agent.",
            "Review and modify as needed before execution.",
            '"""',
            "",
            transforms.imports,
            "from prism.transforms.registry import register_transform",
            "",
            "",
        ]

        for t in transforms.transforms:
            lines.append(f"# {t.row_label} ({t.deliverable_id})")
            if t.notes:
                lines.append(f"# NOTE: {t.notes}")
            if t.confidence == "low":
                lines.append("# WARNING: Low confidence - needs review")

            lines.append(f'@register_transform("{t.element_id}_gold")')
            lines.append(t.code)
            lines.append("")
            lines.append("")

        return "\n".join(lines)

    def save_python_file(
        self,
        transforms: SchemaGoldTransforms,
        output_dir: str = "generated/gold",
    ) -> str:
        """Save generated transforms to Python file.

        Args:
            transforms: SchemaGoldTransforms from generation
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
