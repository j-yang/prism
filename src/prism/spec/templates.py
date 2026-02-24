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


TEMPLATE_BATCH_VARIABLES = """## Task: Generate All Variables from Mock Shell Elements

### Study Information
- Protocol: {protocol_no}
- Title: {study_title}

### Extracted Elements from Mock Shell
These elements are extracted from all deliverables (tables, listings, figures):
```json
{elements_json}
```

### Available ALS Variables
```json
{als_vars_json}
```

### Learned Patterns
```json
{patterns_json}
```

### Your Tasks

Generate ALL silver variables and params needed for this study in one batch.

1. **silver_variables**: For each unique element, create a silver variable
   - Use descriptive snake_case names (e.g., age, sex, cohort, teae_flg, sae_flg)
   - For simple mappings (age, sex), just reference the ALS field
   - For derived flags (Any AE, Any SAE), write CASE WHEN derivation
   - Include the `used_in` list showing which deliverables use this variable
   
   ```json
   [
     {{
       "var_name": "age",
       "schema": "baseline",
       "label": "Age (years)",
       "data_type": "INTEGER",
       "derivation": "",
       "source_vars": ["DM.AGE"],
       "used_in": ["14.1.2.1", "14.1.2.2"],
       "confidence": "high"
     }},
     {{
       "var_name": "sae_flg",
       "schema": "occurrence",
       "label": "Serious Adverse Event Flag",
       "data_type": "TEXT",
       "derivation": "CASE WHEN AESER = 'Yes' THEN 'Y' ELSE 'N' END",
       "source_vars": ["AESER"],
       "used_in": ["14.3.1"],
       "confidence": "high"
     }}
   ]
   ```

2. **params**: For longitudinal parameters (from figures)
   - Extract from figure titles like "Line Plot of PhGA Overtime"
   - Create param definitions with paramcd, parameter, category, unit
   
   ```json
   [
     {{
       "paramcd": "PHGA",
       "parameter": "Physician Global Assessment",
       "category": "Efficacy",
       "unit": "cm",
       "source_form": "PhGA Form",
       "used_in": ["14.2.1", "14.2.15"]
     }}
   ]
   ```

3. **study_config**: Population and event period definitions
   
   ```json
   {{
     "populations": [
       {{"name": "Safety Set", "selection": "received_infusion = 'Y' AND has_safety_eval = 'Y'"}},
       {{"name": "Full Analysis Set", "selection": "received_infusion = 'Y'"}}
     ],
     "event_periods": [
       {{"name": "post_dose", "selection": "ae_start_date >= infusion_date"}},
       {{"name": "pre_dose", "selection": "ae_end_date < infusion_date"}}
     ]
   }}
   ```

### Important Rules

1. **Deduplicate**: Each var_name should be unique. If same concept appears in multiple deliverables, create ONE variable.
2. **Schema assignment**:
   - baseline: Demographics, baseline characteristics (age, sex, disease_duration)
   - occurrence: AE, CM, any event-based data (sae_flg, teae_flg, conmed_name)
   - longitudinal: Repeated measures over time (handled via params, not silver_variables)
3. **Confidence levels**:
   - high: Direct ALS mapping or standard derivation
   - medium: Assumed derivation, needs verification
   - low: Uncertain, requires human review

### Output Format

Return ONLY valid JSON:
{{
  "silver_variables": [...],
  "params": [...],
  "study_config": {{...}},
  "confidence_notes": ["Items needing review"]
}}
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
    elements_json: str = "[]",
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
        elements_json=elements_json,
    )
