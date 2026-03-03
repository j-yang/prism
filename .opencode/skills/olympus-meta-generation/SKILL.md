---
name: olympus-meta-generation
description: Use when generating metadata definitions from mock shell documents for clinical trial data
---

# Olympus Meta Generation

## Overview

Generate MetaDefinitions from mock shell documents using MCP tools and LLM analysis.

**Core principle:** Generate accurate BUSINESS LOGIC descriptions, not code implementation.

---

## ⚠️ CRITICAL: Derivation Types

There are **4 types** of derivations. Use the SIMPLEST type that fits.

### 1. Direct（直接赋值）

**Simple column mapping.** No derivation_logic needed.

**When to use:** Variable is a direct rename or simple type cast.

**Example:**
```python
SilverVariableDefinition(
    var_name="subject_identifier",
    derivation_type="direct",
    source_vars="DM.SUBJID",
    derivation_logic=None  # ✅ No logic needed for direct
)
```

---

### 2. Conditional（条件判断）

**If-then-else logic.** Use arrow notation: `condition → value`

**When to use:** Variable requires conditional logic (flag, category, etc.)

**Format:**
```
condition → value
condition → value
otherwise → default_value
```

**Examples:**

```python
# Simple flag
SilverVariableDefinition(
    var_name="teae_flg",
    derivation_type="conditional",
    source_vars="AE.AESTDTC, EX.EXSTDTC",
    derivation_logic="""
    ae_start_date >= first_dose_date → "Y"
    otherwise → "N"
    """
)

# Multiple conditions
SilverVariableDefinition(
    var_name="severity_category",
    derivation_type="conditional",
    source_vars="AE.AESEV",
    derivation_logic="""
    severity = "Grade 3" OR severity = "Grade 4" OR severity = "Grade 5" → "Severe"
    severity = "Grade 2" → "Moderate"
    otherwise → "Mild"
    """
)

# With edge case handling
SilverVariableDefinition(
    var_name="response_flag",
    derivation_type="conditional",
    source_vars="QS.QSORRES",
    derivation_logic="""
    score >= 20 → "Responder"
    score < 20 → "Non-responder"
    score is missing → "Not evaluated"
    """
)
```

---

### 3. Calculated（计算公式）

**Mathematical formula.** Concise expression.

**When to use:** Variable is calculated from numeric/date fields.

**Format:** Mathematical expression using field names

**Examples:**

```python
# Age calculation
SilverVariableDefinition(
    var_name="age",
    derivation_type="calculated",
    source_vars="DM.BRTHDAT, DM.RFSTDTC",
    derivation_logic="(reference_date - birth_date) / 365.25"
)

# Duration in days
SilverVariableDefinition(
    var_name="ae_duration",
    derivation_type="calculated",
    source_vars="AE.AEENDTC, AE.AESTDTC",
    derivation_logic="end_date - start_date"
)

# Percent change
SilverVariableDefinition(
    var_name="pct_change",
    derivation_type="calculated",
    source_vars="VS.VSORRES, VS.VSBL",
    derivation_logic="((value - baseline) / baseline) * 100"
)

# BMI
SilverVariableDefinition(
    var_name="bmi",
    derivation_type="calculated",
    source_vars="VS.WEIGHT, VS.HEIGHT",
    derivation_logic="weight_kg / (height_m ^ 2)"
)
```

---

### 4. Complex（复杂逻辑）

**Natural language description.** Only for truly complex multi-step logic.

**When to use:** Logic cannot be expressed with above types.

**Format:** Bullet points describing steps/conditions

**Examples:**

```python
SilverVariableDefinition(
    var_name="responder_flag",
    derivation_type="complex",
    source_vars="QS.QSORRES, DM.DISCON",
    derivation_logic="""
    Responder if ALL conditions met:
    - ≥20% improvement in at least 3 core measures at Week 24
    - No worsening (<20% decline) in any individual measure
    - No discontinuation due to AE or lack of efficacy
    """
)

SilverVariableDefinition(
    var_name="disease_activity",
    derivation_type="complex",
    source_vars="LB.LBTEST, VS.VSTEST",
    derivation_logic="""
    Calculate composite disease activity score:
    1. Sum scores from 6 core measures
    2. Normalize to 0-100 scale
    3. Categorize: 0-25=Low, 26-50=Moderate, 51-100=High
    """
)
```

**⚠️ RESTRICTION:** Only use `complex` when truly necessary. If logic can be expressed with conditional/calculated, use those instead.

---

## ALS Lookup Strategy

**ALWAYS use `lookup_als_field` to find source fields.**

### Query Pattern

```python
# Find specific domain fields
lookup_als_field(
    als_path="path/to/ALS.xlsx",
    domain="AE",  # Optional: DM, AE, EX, LB, VS, QS
    keywords="start date"  # Comma-separated keywords
)
```

### Common Domains

- **DM** - Demographics (subject info, age, sex, race)
- **AE** - Adverse Events
- **EX** - Exposure (treatment, dosing)
- **LB** - Laboratory tests
- **VS** - Vital signs
- **QS** - Questionnaires

---

## Process for Each Variable

### Step 1: Understand Clinical Meaning

- Read mock shell column name
- Understand context (population, deliverable type)
- Note footnotes or programming notes

### Step 2: Lookup ALS Fields

```python
lookup_als_field(domain=domain, keywords=keywords)
```

### Step 3: Determine Derivation Type

- **Direct** → Simple mapping
- **Conditional** → If-then logic
- **Calculated** → Math formula
- **Complex** → Multi-step logic

### Step 4: Write Derivation Logic

**For Direct:**
- `derivation_logic = None`
- Just specify `source_vars`

**For Conditional:**
- Use arrow notation: `condition → value`
- Always include `otherwise → default`

**For Calculated:**
- Write concise formula
- Use field names

**For Complex:**
- Bullet points
- Clear steps

### Step 5: Set Confidence

**High:**
- Clear clinical meaning
- ALS fields found
- Standard logic

**Medium:**
- Some ambiguity
- ALS fields not exact match
- Non-standard logic

**Low:**
- Clinical meaning unclear
- ALS fields not found
- Complex or unusual logic
- Requires clinical review

---

## Example Workflows

### Example 1: Subject Identifier (Direct)

```python
# 1. Clinical meaning: Unique subject ID
# 2. ALS lookup: lookup_als_field(domain="DM", keywords="subject")
#    Found: DM.SUBJID
# 3. Derivation type: Direct (simple mapping)
# 4. Logic: None needed

SilverVariableDefinition(
    var_name="subject_identifier",
    var_label="Subject Identifier",
    schema="baseline",
    data_type="TEXT",
    description="Unique subject identifier",
    derivation_type="direct",
    source_vars="DM.SUBJID",
    derivation_logic=None,
    confidence="high"
)
```

---

### Example 2: Age (Calculated)

```python
# 1. Clinical meaning: Age at baseline in years
# 2. ALS lookup: 
#    - lookup_als_field(domain="DM", keywords="birth") → DM.BRTHDAT
#    - lookup_als_field(domain="DM", keywords="reference") → DM.RFSTDTC
# 3. Derivation type: Calculated (math formula)
# 4. Logic: Simple division

SilverVariableDefinition(
    var_name="age",
    var_label="Age",
    schema="baseline",
    data_type="INTEGER",
    description="Age in years at reference date",
    derivation_type="calculated",
    source_vars="DM.BRTHDAT, DM.RFSTDTC",
    derivation_logic="(reference_date - birth_date) / 365.25",
    confidence="high"
)
```

---

### Example 3: TEAE Flag (Conditional)

```python
# 1. Clinical meaning: Treatment emergent AE flag
# 2. ALS lookup:
#    - lookup_als_field(domain="AE", keywords="start") → AE.AESTDTC
#    - lookup_als_field(domain="EX", keywords="dose") → EX.EXSTDTC
# 3. Derivation type: Conditional (if-then logic)
# 4. Logic: Date comparison

SilverVariableDefinition(
    var_name="teae_flg",
    var_label="Treatment Emergent AE Flag",
    schema="occurrence",
    data_type="TEXT",
    description="Flag if AE started on or after first dose",
    derivation_type="conditional",
    source_vars="AE.AESTDTC, EX.EXSTDTC",
    derivation_logic="""
    ae_start_date >= first_dose_date → "Y"
    otherwise → "N"
    """,
    confidence="high"
)
```

---

### Example 4: Severity Category (Conditional)

```python
# 1. Clinical meaning: Group severity grades
# 2. ALS lookup: lookup_als_field(domain="AE", keywords="severity") → AE.AESEV
# 3. Derivation type: Conditional (multiple conditions)
# 4. Logic: Grade grouping

SilverVariableDefinition(
    var_name="severity_category",
    var_label="Severity Category",
    schema="occurrence",
    data_type="TEXT",
    description="Grouped severity category",
    derivation_type="conditional",
    source_vars="AE.AESEV",
    derivation_logic="""
    severity = "Grade 3" OR severity = "Grade 4" OR severity = "Grade 5" → "Severe"
    severity = "Grade 2" → "Moderate"
    otherwise → "Mild"
    """,
    confidence="high"
)
```

---

## Process Overview

### Phase 1: Generate Metadata

1. **Extract mock shell**
   ```python
   extract_mock_shell(mock_path="path/to/shell.docx")
   ```

2. **Analyze deliverables**
   - Review deliverable IDs, types, titles
   - Understand table structures
   - Note populations and footnotes

3. **For each variable:**
   - Understand clinical context
   - Lookup ALS fields
   - Determine derivation type
   - Write derivation logic (keep it SIMPLE)
   - Set confidence level

4. **Validate metadata**
   - Check completeness
   - Verify derivation types are correct
   - Ensure logic is clear and concise

5. **Save to Excel**
   - Use proper sheet names
   - Include `review_needed` sheet for low confidence items

### Phase 2: Review and Iterate

1. **Show low confidence items**
2. **Discuss with user**
3. **Update metadata**

---

## Required MCP Tools

- `extract_mock_shell` - Extract mock shell to JSON
- `lookup_als_field` - Query ALS for source fields
- `save_meta_definitions` - Save to Excel

---

## Tips

### DO:
✅ Use SIMPLEST derivation type that fits  
✅ Use `lookup_als_field` for EVERY variable  
✅ Keep derivation_logic CONCISE  
✅ Use arrow notation for conditionals: `condition → value`  
✅ Use formulas for calculated: `(a - b) / c`  
✅ Set confidence based on certainty  
✅ Mark complex derivations as low confidence  

### DON'T:
❌ Use `complex` when conditional/calculated works  
❌ Write verbose logic descriptions  
❌ Include implementation details  
❌ Use programming syntax (Polars, Pandas, etc.)  
❌ Guess source fields without ALS lookup  
❌ Mark everything as high confidence  

---

## Quality Checklist

Before saving metadata, verify:

- [ ] All variables have `var_name`, `var_label`, `schema`, `data_type`
- [ ] All variables have `description`
- [ ] `derivation_type` is correct (direct/conditional/calculated/complex)
- [ ] `derivation_logic` matches derivation_type:
  - direct → None
  - conditional → arrow notation
  - calculated → formula
  - complex → bullet points
- [ ] `source_vars` lists all fields used in logic
- [ ] `confidence` is set appropriately
- [ ] Logic is CLEAR and CONCISE

---

## Remember

**You are Athena, the Meta Guardian.**

**Your job:**
- Understand BUSINESS logic
- Describe WHAT to do (not HOW)
- Keep it SIMPLE and ACCURATE

**Ares (Silver Agent) will:**
- Read your derivation_logic
- Generate the code
- Handle implementation details

**Focus on ACCURACY of business logic, not code implementation.**
