"""LLM Prompt Templates for Definition Generation.

These templates are used by DefinitionAgent to generate
meta definitions from mock shells.
"""

TEMPLATE_BATCH_DELIVERABLES = """## Task: Generate Meta Definitions from Mock Shell

### Study Information
- Protocol: {protocol_no}
- Title: {study_title}

### Mock Shell Deliverables ({num_deliverables} items)
```json
{deliverables_json}
```

### Extracted Elements
```json
{elements_json}
```

---

## Instructions

You are analyzing mock shell documents to generate meta DEFINITIONS.

For each element in the mock shell:

1. **Understand the semantic meaning**
   - Use table structure, row/column labels
   - Consider footnotes and programming notes
   - Understand the clinical context

2. **Classify the element**
   - **variable**: One-time measurement (demographics, baseline characteristics)
   - **param**: Repeated measurement over time (lab values, vital signs)
   - **flag**: Binary indicator (Y/N flags, occurrence flags)

3. **Determine schema**
   - **baseline**: Single measurement per subject (age, sex, race)
   - **occurrence**: Events that can occur multiple times (AE, CM, MH)
   - **longitudinal**: Repeated measurements (use params, not silver_variables)

4. **Infer data type**
   - TEXT: Categories, labels, strings
   - INTEGER: Counts, ages, whole numbers
   - FLOAT: Measurements, scores, decimals
   - DATE: Dates, datetime strings

5. **Write clear description**
   - Describe what the variable represents
   - NOT how to derive it (that's for later)
   - Use clinical terminology

6. **Assign confidence**
   - **high**: Standard clinical variables (age, sex, AE terms)
   - **medium**: Clear meaning but needs verification
   - **low**: Uncertain, ambiguous, needs human review

7. **Generate Gold Statistics**
   - For each table row, define what statistics to calculate
   - Common statistics: n, %, mean, median, SD, range
   - Specify group_by columns (treatment group, visit, etc.)

---

## Output Schema

Generate JSON matching this EXACT structure:

```json
{{
  "silver_variables": [
    {{
      "var_name": "snake_case_name",
      "var_label": "Human Readable Label",
      "schema": "baseline|occurrence|longitudinal",
      "data_type": "TEXT|INTEGER|FLOAT|DATE",
      "description": "What this variable represents",
      "used_in": ["14.1.2.1", "14.3.1"],
      "confidence": "high|medium|low",
      "source_vars": null,
      "transformation": null,
      "transformation_type": "direct",
      "param_ref": null
    }}
  ],
  "params": [
    {{
      "paramcd": "PARAM",
      "parameter": "Full Parameter Name",
      "category": "Efficacy|Safety|PK|PD",
      "unit": "mg/dL",
      "used_in": ["14.3.1"]
    }}
  ],
  "gold_statistics": [
    {{
      "element_id": "var_name_or_paramcd",
      "element_type": "variable|param|flag",
      "row_label": "Row label in table",
      "schema": "baseline|occurrence|longitudinal",
      "statistics": {{"n": true, "%": true, "mean": false}},
      "group_by": ["treatment_group"],
      "deliverable_id": "14.1.2.1",
      "confidence": "high",
      "group_id": "all",
      "population": null,
      "selection": null
    }}
  ],
  "platinum_deliverables": [
    {{
      "deliverable_id": "14.1.2.1",
      "deliverable_type": "table|listing|figure",
      "title": "Full title",
      "population": "Safety Set",
      "schema": "baseline",
      "elements": []
    }}
  ],
  "confidence_notes": [
    "Items that need human review"
  ]
}}
```

---

## Examples

### Good Variable Definition:
```json
{{
  "var_name": "teae_flg",
  "var_label": "Treatment-Emergent AE Flag",
  "schema": "occurrence",
  "data_type": "TEXT",
  "description": (
      "Indicates whether the adverse event is "
      "treatment-emergent, defined as any AE with onset "
      "on or after the first dose of study drug"
  ),
  "used_in": ["14.3.1"],
  "confidence": "high"
}}
```

### Good Param Definition:
```json
{{
  "paramcd": "ALT",
  "parameter": "Alanine Aminotransferase",
  "category": "Safety",
  "unit": "U/L",
  "used_in": ["14.3.2"]
}}
```

### Good Gold Statistic Definition:
```json
{{
  "element_id": "teae_flg",
  "element_type": "flag",
  "row_label": "Treatment-Emergent AE",
  "schema": "occurrence",
  "statistics": {{"n": true, "%": true}},
  "group_by": ["treatment_group"],
  "deliverable_id": "14.3.1",
  "confidence": "high"
}}
```

---

## Important Notes

1. Output ONLY valid JSON (no markdown, no explanations)
2. Use snake_case for var_name (e.g., teae_flg, age_years)
3. DO NOT try to map to ALS fields or data sources
4. Focus on WHAT the variable is, not HOW to derive it
5. If uncertain, set confidence to "low" and add to confidence_notes
6. Keep var_name concise (max 30 characters)
7. For longitudinal data, use params instead of silver_variables

Generate the JSON now:
"""
