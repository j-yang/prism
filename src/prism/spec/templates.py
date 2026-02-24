"""LLM Prompt Templates for Spec Generation."""

from typing import Optional


SYSTEM_PROMPT = """You are a clinical trial specification expert. Your task is to generate structured specifications from mock shell documents for clinical trial data analysis.

You follow these conventions:
1. Variable naming: snake_case, descriptive (e.g., ae_related_to_cart, teae_flg)
2. Schema types: baseline, longitudinal, occurrence
3. Element types: variable (regular), param (longitudinal parameter), flag (derived indicator)
4. Statistics: Use JSON format like {"n": "count", "pct": "percent"} or {"mean": "avg", "sd": "std"}

Always respond in valid JSON format as specified in each task."""


TEMPLATE_GENERATE_SPEC = """## Task: Generate Clinical Trial Spec

### Input Context

**Study Information:**
- Protocol: {protocol_no}
- Title: {study_title}

**Deliverable to Process:**
```json
{deliverable_json}
```

**Available ALS Variables:**
```json
{als_vars_json}
```

**Learned Patterns (from previous studies):**
```json
{patterns_json}
```

### Your Tasks

Generate specifications for this deliverable. Respond with a JSON object containing:

1. **platinum**: The deliverable definition
   ```json
   {{
     "deliverable_id": "14.3.1",
     "deliverable_type": "table",
     "title": "Overall Summary of Adverse Events",
     "population": "Safety Set",
     "schema": "occurrence"
   }}
   ```

2. **silver_variables**: List of silver variables needed
   - For each row in the deliverable, determine if it needs a new derived variable
   - Check ALS variables for direct mappings first
   - Use descriptive snake_case names
   ```json
   [
     {{
       "var_name": "teae_flg",
       "schema": "occurrence", 
       "label": "Treatment Emergent Adverse Event Flag",
       "data_type": "TEXT",
       "derivation": "CASE WHEN ae_start_date >= infusion_date THEN 'Y' ELSE 'N' END",
       "source_vars": ["ae_start_date", "infusion_date"],
       "confidence": "high"
     }}
   ]
   ```

3. **gold_statistics**: Statistics definitions for each row
   ```json
   [
     {{
       "deliverable_id": "14.3.1",
       "row_label": "Any AE",
       "element_type": "flag",
       "element_id": "teae_flg", 
       "selection": "teae_flg = 'Y'",
       "statistics": {{"n": "count", "pct": "percent"}},
       "group_by": ["cohort"]
     }}
   ]
   ```

4. **params**: Any longitudinal parameters needed (if this is a longitudinal deliverable)
   ```json
   [
     {{
       "paramcd": "MRSS",
       "parameter": "Modified Rodnan Skin Score",
       "category": "Efficacy",
       "unit": "points",
       "source_form": "mRSS Form"
     }}
   ]
   ```

5. **study_config**: Population and visit definitions referenced
   ```json
   {{
     "populations": [
       {{"name": "Safety Set", "selection": "received_infusion = 'Y' AND has_safety_eval = 'Y'"}}
     ],
     "event_periods": [
       {{"name": "post_dose", "selection": "ae_start_date >= infusion_date"}}
     ]
   }}
   ```

### Output Format

Return ONLY valid JSON (no markdown code blocks):
{{
  "platinum": {{...}},
  "silver_variables": [...],
  "gold_statistics": [...],
  "params": [...],
  "study_config": {{...}},
  "confidence_notes": ["Any items that need human review"]
}}
"""


TEMPLATE_MATCH_ALS = """## Task: Match Variables to ALS

### ALS Variable Dictionary:
```json
{als_dict_json}
```

### Variables to Match:
```json
{variables_json}
```

### Task

For each variable, find the best matching ALS field(s) based on:
1. Label similarity (semantic match)
2. Context from the deliverable

Return JSON:
```json
[
  {{
    "var_name": "age",
    "matched": true,
    "als_field": "DM.AGE",
    "als_label": "Age",
    "confidence": "high",
    "notes": "Direct match on label"
  }},
  {{
    "var_name": "teae_flg",
    "matched": false,
    "als_field": null,
    "als_label": null,
    "confidence": "n/a",
    "notes": "Derived variable, no direct ALS match"
  }}
]
```

Return ONLY valid JSON.
"""


TEMPLATE_LEARN_DIFF = """## Task: Learn from Human Corrections

### Original Generated Spec:
```json
{original_json}
```

### Human-Corrected Spec:
```json
{corrected_json}
```

### Task

Identify what was changed and extract patterns that can be applied to future studies.

Focus on:
1. Variable naming corrections
2. Derivation logic improvements  
3. Selection criteria refinements
4. Statistics definition changes

Return JSON:
```json
{{
  "patterns": [
    {{
      "pattern_type": "naming",
      "input_pattern": "Any AE related to CART therapy",
      "original_output": "ae_cart_related_flg",
      "corrected_output": "ae_related_to_cart",
      "rule": "Use 'related_to' instead of 'related' for relationship flags"
    }},
    {{
      "pattern_type": "derivation",
      "input_pattern": "TEAE definition",
      "original_output": "ae_start_date >= infusion_date",
      "corrected_output": "CASE WHEN ae_start_date >= infusion_date OR (ae_start_date = infusion_date AND ae_before_infusion = 'N') THEN 'Y' ELSE 'N' END",
      "rule": "TEAE must also check same-day cases"
    }}
  ],
  "summary": "2 patterns learned"
}}
```

Return ONLY valid JSON.
"""


def format_prompt(
    template: str,
    protocol_no: str = "",
    study_title: str = "",
    deliverable_json: str = "{}",
    als_vars_json: str = "{}",
    als_dict_json: str = "{}",
    variables_json: str = "[]",
    patterns_json: str = "[]",
    original_json: str = "{}",
    corrected_json: str = "{}",
) -> str:
    """Format a prompt template with provided values."""
    return template.format(
        protocol_no=protocol_no,
        study_title=study_title,
        deliverable_json=deliverable_json,
        als_vars_json=als_vars_json,
        als_dict_json=als_dict_json,
        variables_json=variables_json,
        patterns_json=patterns_json,
        original_json=original_json,
        corrected_json=corrected_json,
    )
