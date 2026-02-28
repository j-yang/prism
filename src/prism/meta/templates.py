"""LLM Prompt Templates for Spec Generation.

Templates output JSON matching meta schema exactly.
"""

SYSTEM_PROMPT = """You are a clinical trial specification expert. Generate structured specifications from mock shell documents.

CRITICAL: Output ONLY valid JSON matching the schema exactly. No markdown, no explanations.

Field naming rules:
- var_name: snake_case (e.g., teae_flg, ae_related_to_cart)
- schema: baseline | occurrence | longitudinal
- data_type: TEXT | INTEGER | FLOAT | DATE
- transformation: Python code (not SQL) or empty for direct mapping
- transformation_type: direct | python | rule_doc
- source_vars: comma-separated ALS fields (e.g., "DM.AGE, DM.SEX")
"""


TEMPLATE_BATCH_VARIABLES = """## Task: Generate Silver Variables from Mock Shell Elements

### Study Information
- Protocol: {protocol_no}
- Title: {study_title}

### Extracted Elements from Mock Shell
```json
{elements_json}
```

### Available ALS Variables
```json
{als_vars_json}
```

---

## Output Schema

Generate JSON with this structure:

```json
{{
  "silver_variables": [
    {{
      "var_name": "snake_case_name",
      "var_label": "Human readable label",
      "schema": "baseline|occurrence|longitudinal",
      "data_type": "TEXT|INTEGER|FLOAT|DATE",
      "source_vars": "DM.AGE, DM.SEX",
      "transformation": "Python code or empty",
      "transformation_type": "direct|python",
      "param_ref": "",
      "description": "",
      "confidence": "high|medium|low"
    }}
  ],
  "params": [
    {{
      "paramcd": "CODE",
      "parameter": "Full parameter name",
      "category": "Efficacy|Safety|PK|PD",
      "unit": "unit",
      "default_source_form": "",
      "default_source_var": ""
    }}
  ],
  "confidence_notes": ["Items needing review"]
}}
```

---

## Examples

### Example 1: Direct Mapping
Element: "Age (years)"
Output:
```json
{{"var_name": "age", "var_label": "Age (years)", "schema": "baseline", "data_type": "INTEGER", "source_vars": "DM.AGE", "transformation": "", "transformation_type": "direct", "confidence": "high"}}
```

### Example 2: Derived Flag
Element: "Treatment Emergent Adverse Event"
Output:
```json
{{"var_name": "teae_flg", "var_label": "Treatment Emergent AE Flag", "schema": "occurrence", "data_type": "TEXT", "source_vars": "AE.AESTDTC, EX.EXSTDTC", "transformation": "pl.when(pl.col('ae_start_date') >= pl.col('infusion_date')).then(pl.lit('Y')).otherwise(pl.lit('N'))", "transformation_type": "python", "confidence": "high"}}
```

### Example 3: SAE Flag
Element: "Any SAE"
Output:
```json
{{"var_name": "sae_flg", "var_label": "Serious Adverse Event Flag", "schema": "occurrence", "data_type": "TEXT", "source_vars": "AE.AESER", "transformation": "pl.when(pl.col('AE_AESER') == 'Y').then(pl.lit('Y')).otherwise(pl.lit('N'))", "transformation_type": "python", "confidence": "high"}}
```

### Example 4: AE Related to CAR-T
Element: "Any AE related to CAR-T therapy"
Output:
```json
{{"var_name": "ae_related_to_cart", "var_label": "AE Related to CAR-T", "schema": "occurrence", "data_type": "TEXT", "source_vars": "AE.AEREL", "transformation": "pl.when(pl.col('AE_AEREL').is_in(['Related', 'Possibly Related', 'Probably Related'])).then(pl.lit('Y')).otherwise(pl.lit('N'))", "transformation_type": "python", "confidence": "high"}}
```

### Example 5: Calculated Duration
Element: "Follow-up duration (months)"
Output:
```json
{{"var_name": "follow_up_duration_months", "var_label": "Follow-up Duration (months)", "schema": "baseline", "data_type": "INTEGER", "source_vars": "EX.EXSTDTC, DS.DSSTDTC", "transformation": "(pl.col('last_visit_date') - pl.col('infusion_date')).dt.total_days() // 30", "transformation_type": "python", "confidence": "medium"}}
```

### Example 6: Concomitant Medication Flag
Element: "Concomitant Glucocorticoid Use"
Output:
```json
{{"var_name": "concomitant_glucocorticoid_flg", "var_label": "Concomitant Glucocorticoid", "schema": "occurrence", "data_type": "TEXT", "source_vars": "CM.CMTRT", "transformation": "pl.when(pl.col('CM_CMTRT').str.to_lowercase().str.contains('glucocorticoid|steroid|prednisone')).then(pl.lit('Y')).otherwise(pl.lit('N'))", "transformation_type": "python", "confidence": "medium"}}
```

---

## Rules

1. **var_name**: snake_case, descriptive, suffix with _flg for flags
2. **schema**: 
   - baseline = demographics, one-time measurements
   - occurrence = AE, CM, events
   - longitudinal = repeated measures (use params, not silver_variables)
3. **transformation**: Use Polars Python syntax:
   - `pl.when(condition).then(value).otherwise(default)`
   - `pl.col('field')` for column reference
   - `.str.contains('pattern')` for string matching
   - `.is_in(['A', 'B'])` for value lists
   - `.dt.total_days()` for date differences
4. **source_vars**: Comma-separated ALS field names (DOMAIN.FIELD)
5. **transformation_type**: 
   - "direct" = simple mapping, transformation empty
   - "python" = derived, transformation contains Python code
6. **confidence**: 
   - "high" = direct mapping or standard derivation
   - "medium" = assumed logic, needs verification
   - "low" = uncertain, requires human review

---

## Output

Return ONLY valid JSON (no markdown code blocks).
"""


TEMPLATE_GOLD_BATCH = """## Task: Generate Gold Statistics for {num_deliverables} Deliverables

### Deliverables
```json
{deliverables_json}
```

### Available Silver Variables
```json
{vars_json}
```

### Available Parameters
```json
{params_json}
```

---

## Output Schema

Return JSON array with one entry per deliverable:

```json
{{
  "deliverables": [
    {{
      "platinum": {{
        "deliverable_id": "14.1.1",
        "deliverable_type": "table|listing|figure",
        "title": "Title",
        "schema": "baseline|occurrence|longitudinal",
        "population": "Safety Set",
        "elements": []
      }},
      "gold_statistics": [
        {{
          "element_id": "var_name",
          "group_id": "Treatment Group",
          "schema": "baseline",
          "population": "Safety Set",
          "selection": "",
          "statistics": {{"n": "count", "pct": "percent"}},
          "deliverable_id": "14.1.1",
          "row_label": "Age",
          "element_type": "variable"
        }}
      ],
      "confidence_notes": []
    }}
  ]
}}
```

---

## Rules

1. **deliverable_type**: table, listing, or figure
2. **statistics**:
   - Listings: {{"value": "raw"}}
   - Tables: {{"n": "count", "pct": "percent"}}
   - Figures: {{"mean": "avg", "sd": "std"}}
3. **element_type**: variable, param, or flag
4. **element_id**: Match to silver variable var_name or paramcd
5. **group_id**: Treatment group column name

---

## Output

Return ONLY valid JSON array.
"""


def format_prompt(template: str, **kwargs) -> str:
    """Format a prompt template with provided values."""
    return template.format(**kwargs)
