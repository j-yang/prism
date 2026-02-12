# PRISM-DB Database Schema Reference

**Version**: 3.0  
**Date**: 2026-02-12

---

## Schema Overview

PRISM-DB uses DuckDB with the following schema namespaces:

| Schema | Purpose | Table Count |
|--------|---------|-------------|
| `bronze` | Raw EDC data (as-collected) | ~10-30 per study |
| `silver` | Analysis-ready subject-level data | 3 (baseline, longitudinal, occurrence) |
| `gold` | Group-level aggregated statistics | 3 (baseline, longitudinal, occurrence) |
| `meta` | Metadata (schema docs, derivations, outputs) | 5 core tables |

---

## Bronze Schema

### Purpose
Store raw EDC data with minimal transformation, preserving original form structure.

### Table Naming Convention
`bronze.{form_name}` - Direct mapping from EDC form OID

### Common Columns
Every bronze table includes:
```sql
usubjid TEXT,
study_code TEXT,
import_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

### Example Tables
- `bronze.demog` - Demographics form
- `bronze.vs` - Vital signs
- `bronze.labs` - Laboratory data
- `bronze.ae` - Adverse events
- `bronze.cm` - Concomitant medications

---

## Silver Schema

### Purpose
Subject-level analysis-ready datasets with derived variables.

### Tables

#### silver.baseline
**Granularity**: 1 row per subject

```sql
CREATE TABLE silver.baseline (
    usubjid TEXT PRIMARY KEY,
    study_code TEXT,
    
    -- Demographics
    age INTEGER,
    sex TEXT,
    race TEXT,
    ethnic TEXT,
    
    -- Treatment
    trtsdt DATE,
    trtedt DATE,
    trtdur INTEGER,
    trta TEXT,
    trtp TEXT,
    
    -- Flags
    saffl TEXT,
    fasfl TEXT,
    ppsfl TEXT,
    
    -- Baseline values
    bl_weight REAL,
    bl_height REAL,
    bl_bmi REAL,
    
    -- Metadata
    derivation_timestamp TIMESTAMP,
    derivation_version TEXT
);
```

#### silver.longitudinal
**Granularity**: 1 row per subject × parameter × visit

```sql
CREATE TABLE silver.longitudinal (
    id INTEGER PRIMARY KEY,
    usubjid TEXT NOT NULL,
    study_code TEXT,
    
    paramcd TEXT NOT NULL,
    param TEXT,
    paramcat TEXT,
    
    visit TEXT,
    visitnum INTEGER,
    adt DATE,
    ady INTEGER,
    
    aval REAL,
    avalc TEXT,
    
    base REAL,
    chg REAL,
    pchg REAL,
    
    ablfl TEXT,
    anl01fl TEXT,
    
    derivation_timestamp TIMESTAMP,
    UNIQUE(usubjid, paramcd, visit)
);
```

#### silver.occurrence
**Granularity**: 1 row per event

```sql
CREATE TABLE silver.occurrence (
    id INTEGER PRIMARY KEY,
    usubjid TEXT NOT NULL,
    study_code TEXT,
    
    domain TEXT NOT NULL,
    seq INTEGER,
    
    term TEXT,
    decod TEXT,
    cat TEXT,
    scat TEXT,
    
    astdt DATE,
    aendt DATE,
    astdy INTEGER,
    aendy INTEGER,
    
    -- Flags
    teaefl TEXT,
    saefl TEXT,
    relfl TEXT,
    serfl TEXT,
    dthfl TEXT,
    
    derivation_timestamp TIMESTAMP,
    UNIQUE(usubjid, domain, seq)
);
```

---

## Gold Schema

### Purpose
Group-level aggregated statistics in long-table format.

### Design Principle
**Long Table** - Each row represents one statistical measure for one group.

### Tables

#### gold.baseline
**Content**: Baseline variable statistics by treatment group

```sql
CREATE TABLE gold.baseline (
    output_id TEXT,
    
    group1_name TEXT,
    group1_value TEXT,
    group2_name TEXT,
    group2_value TEXT,
    
    comparison TEXT,
    
    variable TEXT,
    category TEXT,
    
    stat_name TEXT,
    stat_value REAL,
    stat_display TEXT,
    row_order INTEGER
);
```

**Example Query**:
```sql
-- Get demographics table for output T1_demog
SELECT * FROM gold.baseline
WHERE output_id = 'T1_demog'
ORDER BY variable, group1_value, stat_name, row_order;
```

#### gold.longitudinal
**Content**: Longitudinal parameter statistics by visit

```sql
CREATE TABLE gold.longitudinal (
    output_id TEXT,
    
    group1_name TEXT,
    group1_value TEXT,
    group2_name TEXT,
    group2_value TEXT,
    
    comparison TEXT,
    
    paramcd TEXT,
    visit TEXT,
    
    stat_name TEXT,
    stat_value REAL,
    stat_display TEXT,
    row_order INTEGER
);
```

#### gold.occurrence
**Content**: Event statistics by category

```sql
CREATE TABLE gold.occurrence (
    output_id TEXT,
    
    group1_name TEXT,
    group1_value TEXT,
    group2_name TEXT,
    group2_value TEXT,
    
    comparison TEXT,
    
    cat1_name TEXT,
    cat1_value TEXT,
    cat2_name TEXT,
    cat2_value TEXT,
    
    stat_name TEXT,
    stat_value REAL,
    stat_display TEXT,
    row_order INTEGER
);
```

---

## Meta Schema

### Purpose
Store metadata for schema documentation, derivations, and output specifications.

### Tables

#### meta.schema_docs
**Purpose**: Document database structure for each layer

```sql
CREATE TABLE meta.schema_docs (
    layer TEXT,
    table_name TEXT,
    column_name TEXT,
    data_type TEXT,
    description TEXT,
    source TEXT,
    example_values TEXT,
    PRIMARY KEY (layer, table_name, column_name)
);
```

#### meta.data_catalog
**Purpose**: Variable registry across all layers

```sql
CREATE TABLE meta.data_catalog (
    var_name TEXT,
    schema TEXT,
    layer TEXT,
    label TEXT,
    data_type TEXT,
    source_form TEXT,
    source_field TEXT,
    codelist TEXT,
    is_derived BOOLEAN,
    derivation_id TEXT,
    study_code TEXT,
    PRIMARY KEY (var_name, schema, layer, study_code)
);
```

#### meta.derivations
**Purpose**: Transformation rules for Silver layer generation

```sql
CREATE TABLE meta.derivations (
    derivation_id TEXT PRIMARY KEY,
    target_var TEXT,
    target_schema TEXT,
    
    depends_on TEXT,
    transformation_sql TEXT,
    complexity TEXT,
    
    description TEXT,
    rule_doc TEXT,
    
    study_overrides TEXT,
    created_at TIMESTAMP
);
```

#### meta.output_spec
**Purpose**: Define outputs and statistical requirements

```sql
CREATE TABLE meta.output_spec (
    output_id TEXT PRIMARY KEY,
    output_type TEXT,
    schema TEXT,
    
    source_table TEXT,
    required_vars TEXT,
    required_params TEXT,
    filter_condition TEXT,
    
    group_by TEXT,
    comparison TEXT,
    
    stats_required TEXT,
    analysis_method TEXT,
    analysis_spec TEXT,
    
    title_template TEXT,
    footnote_template TEXT,
    
    study_overrides TEXT,
    
    block TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### meta.output_assembly
**Purpose**: Define how to assemble Gold data into final outputs

```sql
CREATE TABLE meta.output_assembly (
    output_id TEXT,
    component_type TEXT,
    component_order INTEGER,
    
    select_condition TEXT,
    layout_template TEXT,
    formatting_rules TEXT,
    
    PRIMARY KEY (output_id, component_order)
);
```

---

## Indexes

### Silver Layer
```sql
CREATE INDEX idx_silver_baseline_study ON silver.baseline(study_code);
CREATE INDEX idx_silver_long_usubjid ON silver.longitudinal(usubjid);
CREATE INDEX idx_silver_long_paramcd ON silver.longitudinal(paramcd);
CREATE INDEX idx_silver_long_visit ON silver.longitudinal(visit);
CREATE INDEX idx_silver_occ_usubjid ON silver.occurrence(usubjid);
CREATE INDEX idx_silver_occ_domain ON silver.occurrence(domain);
```

### Gold Layer
```sql
CREATE INDEX idx_gold_baseline_output ON gold.baseline(output_id);
CREATE INDEX idx_gold_long_output ON gold.longitudinal(output_id);
CREATE INDEX idx_gold_occ_output ON gold.occurrence(output_id);
```

---

## Views (Optional)

### Commonly Used Views

```sql
-- Subject disposition summary
CREATE VIEW v_disposition AS
SELECT 
    study_code,
    trta,
    COUNT(*) as n_randomized,
    SUM(CASE WHEN saffl = 'Y' THEN 1 ELSE 0 END) as n_safety,
    SUM(CASE WHEN fasfl = 'Y' THEN 1 ELSE 0 END) as n_fas
FROM silver.baseline
GROUP BY study_code, trta;

-- Baseline characteristics
CREATE VIEW v_baseline_summary AS
SELECT 
    study_code,
    trta,
    COUNT(*) as n,
    AVG(age) as mean_age,
    STDDEV(age) as sd_age,
    SUM(CASE WHEN sex = 'F' THEN 1 ELSE 0 END) as n_female
FROM silver.baseline
WHERE saffl = 'Y'
GROUP BY study_code, trta;
```

---

## Database Size Estimation

For a typical clinical trial:

| Layer | Tables | Rows/Table | Est. Size |
|-------|--------|------------|-----------|
| Bronze | 20 | 50-5000 | 1-10 MB |
| Silver | 3 | baseline: 100s, longitudinal: 10,000s, occurrence: 1,000s | 5-50 MB |
| Gold | 3 | 1,000s per output | 1-10 MB |
| Meta | 5 | 100s-1000s | <1 MB |

**Total**: ~10-70 MB per study (uncompressed)

DuckDB compression can reduce this by 50-80%.

---

## Schema Migration Strategy

When schema changes are needed:

1. **Add columns** (safe):
```sql
ALTER TABLE silver.baseline ADD COLUMN new_var REAL;
```

2. **Rename columns** (requires care):
```sql
-- Create new column
ALTER TABLE silver.baseline ADD COLUMN new_name TEXT;
-- Copy data
UPDATE silver.baseline SET new_name = old_name;
-- Drop old column
ALTER TABLE silver.baseline DROP COLUMN old_name;
```

3. **Version tracking**:
```sql
ALTER TABLE silver.baseline ADD COLUMN schema_version TEXT DEFAULT '3.0';
```

---

## Backup and Recovery

### Export Data
```sql
COPY (SELECT * FROM silver.baseline) TO 'backup/baseline.parquet' (FORMAT PARQUET);
```

### Import Data
```sql
CREATE TABLE silver.baseline AS SELECT * FROM read_parquet('backup/baseline.parquet');
```

---

## Performance Tips

1. **Use appropriate indexes** on commonly queried columns
2. **Partition large tables** by study_code if multi-study
3. **Use ANALYZE** after large data loads
4. **Monitor query plans** with EXPLAIN ANALYZE
5. **Consider materialized views** for frequently accessed aggregations

---

## See Also

- [ARCHITECTURE.md](../ARCHITECTURE.md) - Overall system architecture
- [PROJECT_PLAN.md](../PROJECT_PLAN.md) - Implementation roadmap
