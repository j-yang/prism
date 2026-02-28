"""PydanticAI agent for Meta generation.

Generates clinical trial metadata from mock shell elements.
Uses batch processing (10 variables per call) for efficiency.
"""

import json
from typing import List, Optional

from pydantic import BaseModel

from prism.agent.base import BaseAgent
from prism.core.models import (
    GeneratedSpec,
    ParamSpec,
    SilverVariableSpec,
)


class BatchVariableResult(BaseModel):
    """Result for batch variable generation (10 variables)."""

    silver_variables: List[SilverVariableSpec] = []
    params: List[ParamSpec] = []
    confidence_notes: List[str] = []


class MetaAgent(BaseAgent):
    """PydanticAI agent for generating metadata."""

    def __init__(
        self,
        provider: str = "deepseek",
        db_path: Optional[str] = None,
        als_path: Optional[str] = None,
    ):
        super().__init__(provider=provider, db_path=db_path, als_path=als_path)

        self.tools.load_als_dict(als_path)

    def _get_system_prompt(self) -> str:
        return """You are a clinical trial metadata expert.

Generate Silver layer variable specifications from mock shell elements.
Use the provided tools to look up ALS fields and verify dependencies.

CRITICAL OUTPUT REQUIREMENTS:
1. Output ONLY valid JSON
2. Match the BatchVariableResult schema exactly
3. No markdown, no explanations outside the JSON

Field naming rules:
- var_name: snake_case (e.g., teae_flg, age_years)
- schema: baseline | occurrence | longitudinal
- data_type: TEXT | INTEGER | FLOAT | DATE | DATETIME
- transformation_type: direct | python | rule_doc
"""

    def generate_batch(
        self,
        elements: List[dict],
        batch_size: int = 10,
    ) -> BatchVariableResult:
        """Generate variables for a batch of elements.

        Args:
            elements: List of element dicts with label, type, used_in, context
            batch_size: Number of elements per batch (default 10)

        Returns:
            BatchVariableResult with silver_variables, params, confidence_notes
        """
        als_vars = list(self.tools._als_dict.values())[:80]
        als_vars_json = json.dumps(als_vars, indent=2, ensure_ascii=False)[:4000]

        elements_json = json.dumps(elements, indent=2, ensure_ascii=False)[:6000]

        prompt = f"""## Task: Generate Silver Variables from Mock Shell Elements

### Available ALS Variables
```json
{als_vars_json}
```

### Extracted Elements
```json
{elements_json}
```

---

## Output Schema

Generate JSON matching this exact structure:
```json
{{
  "silver_variables": [
    {{
      "var_name": "snake_case_name",
      "var_label": "Human readable label",
      "schema": "baseline|occurrence|longitudinal",
      "data_type": "TEXT|INTEGER|FLOAT|DATE",
      "source_vars": "DM.AGE, DM.SEX",
      "transformation": "Python code or empty string",
      "transformation_type": "direct|python",
      "param_ref": "",
      "description": "",
      "confidence": "high|medium|low",
      "used_in": "14.1.1,14.1.2"
    }}
  ],
  "params": [
    {{
      "paramcd": "CODE",
      "parameter": "Full parameter name",
      "category": "Efficacy|Safety|PK|PD",
      "unit": "unit",
      "used_in": "14.1.1"
    }}
  ],
  "confidence_notes": ["Items needing review"]
}}
```

---

## Rules

1. var_name: snake_case, suffix with _flg for flags
2. schema:
   - baseline = demographics, one-time measurements
   - occurrence = AE, CM, events
   - longitudinal = repeated measures (use params, not silver_variables)
3. transformation_type:
   - "direct" = simple mapping, transformation empty
   - "python" = derived, transformation contains Polars code
4. confidence:
   - "high" = direct mapping or standard derivation
   - "medium" = assumed logic, needs verification
   - "low" = uncertain, requires human review

Return ONLY valid JSON (no markdown code blocks).
"""

        return self.run(prompt, result_type=BatchVariableResult)

    def generate_all(
        self,
        elements: List[dict],
        batch_size: int = 10,
    ) -> GeneratedSpec:
        """Generate all variables from elements in batches.

        Args:
            elements: List of element dicts
            batch_size: Number of elements per batch

        Returns:
            GeneratedSpec with all variables combined
        """
        all_silver_vars = []
        all_params = []
        all_notes = []

        for i in range(0, len(elements), batch_size):
            batch = elements[i : i + batch_size]
            print(f"  Batch {i // batch_size + 1}: {len(batch)} elements")

            result = self.generate_batch(batch, batch_size)

            all_silver_vars.extend(result.silver_variables)
            all_params.extend(result.params)
            all_notes.extend(result.confidence_notes)

            print(f"    Generated {len(result.silver_variables)} variables")

        return GeneratedSpec(
            silver_variables=all_silver_vars,
            params=all_params,
            confidence_notes=all_notes,
        )
