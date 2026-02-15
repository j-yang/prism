# PRISM Architecture

## Overview

PRISM is a clinical trial data warehouse built on DuckDB with AI-powered code generation.

## Medallion Architecture

```
                    ┌─────────────────────────────────────────────┐
                    │                  Meta Layer                  │
                    │  11 tables: params, flags, visits,          │
                    │  variables, derivations, outputs, etc.      │
                    └──────────────────────┬──────────────────────┘
                                           │
                    ┌──────────────────────▼──────────────────────┐
                    │                Bronze Layer                  │
                    │  Raw EDC data imported from SAS/CSV/Excel    │
                    │  One table per form: bronze.demog, etc.     │
                    └──────────────────────┬──────────────────────┘
                                           │ Agent generates SQL
                    ┌──────────────────────▼──────────────────────┐
                    │                Silver Layer                  │
                    │  Subject-level derived data                 │
                    │  3 schemas: baseline, longitudinal,         │
                    │             occurrence                      │
                    └──────────────────────┬──────────────────────┘
                                           │ Agent generates Python
                    ┌──────────────────────▼──────────────────────┐
                    │                 Gold Layer                   │
                    │  Group-level statistics                     │
                    │  Long-table format for flexible rendering   │
                    └──────────────────────┬──────────────────────┘
                                           │
                    ┌──────────────────────▼──────────────────────┐
                    │              Platinum Layer                  │
                    │  Report output: RTF, PDF, HTML, Slides      │
                    └─────────────────────────────────────────────┘
```

## Meta Schema (11 Tables)

### Reference Tables (External Linkable)
| Table | Purpose |
|-------|---------|
| `meta.params` | Longitudinal parameter definitions |
| `meta.flags` | Occurrence event flag definitions |
| `meta.visits` | Analysis visit definitions |

### Study-Specific Tables
| Table | Purpose |
|-------|---------|
| `meta.study_info` | Study metadata |
| `meta.variables` | Unified variable registry |
| `meta.derivations` | Transformation rules |
| `meta.outputs` | Output definitions (table/figure/listing) |
| `meta.output_variables` | Output-variable associations |
| `meta.output_params` | Output-parameter associations |
| `meta.functions` | Complex function library |
| `meta.dependencies` | Variable dependency graph |

## Agent System

### Code Generation Flow

```
meta.derivations ──▶ Template Match? ──▶ Yes ──▶ Jinja2 Template
                          │
                          No
                          │
                          ▼
                    DeepSeek LLM ──▶ Generated SQL/Python
                          │
                          ▼
                    Needs Review ( flagged )
```

### Template Types

| Template | Pattern | Example |
|----------|---------|---------|
| direct_copy | "Take", "Equal to" | `SELECT col AS target` |
| coalesce | "Coalesce" | `COALESCE(col1, col2)` |
| recode | "Recode", "Map" | `CASE WHEN...` |
| date_diff | "Date diff" | `DATE_DIFF(day, d1, d2)` |
| combine | "Combine", "Concat" | `CONCAT(a, b)` |
| flag | "Flag", "Y/N" | `CASE WHEN cond THEN 'Y'` |

## Gold Layer Design

### Long Table Format

```sql
CREATE TABLE gold.baseline (
    output_id TEXT,        -- e.g., "T1_demog"
    group1_name TEXT,      -- e.g., "TRTA"
    group1_value TEXT,     -- e.g., "Drug A"
    variable TEXT,         -- e.g., "AGE"
    category TEXT,         -- for categorical vars
    stat_name TEXT,        -- e.g., "n", "mean", "pct"
    stat_value DOUBLE,
    stat_display TEXT,
    row_order INTEGER
);
```

This format supports:
- Multiple grouping variables
- Both continuous and categorical statistics
- Flexible rendering

## Data Flow

```
1. Parse ALS/Spec
   parse_als_to_db() → meta.variables, bronze tables

2. Load Raw Data
   load_sas_to_bronze() → bronze.* tables

3. Define Derivations
   meta.add_derivation() → meta.derivations
j
4. Generate Silver SQL
   SilverGenerator.generate_all() → derive_baseline.sql, etc.

5. Execute Silver SQL
   User runs generated SQL → silver.* tables

6. Define Outputs
   meta.add_output() → meta.outputs

7. Generate Gold Scripts
   GoldEngine.generate_all() → T1_demog.py, etc.

8. Execute Gold Scripts
   User runs generated Python → gold.* tables

9. Render Reports (Future)
   render_output() → RTF/PDF/HTML
```

## File Organization

```
src/prism/
├── core/
│   ├── database.py      # DuckDB connection wrapper
│   ├── schema.py        # Pydantic models
│   └── config.py        # Path helpers
│
├── sql/
│   ├── init_meta.sql    # Meta schema DDL
│   ├── init_gold.sql    # Gold schema DDL
│   └── init_traceability.sql
│
├─:echo mapcheck("<C-h>", "n")─ agent/
│   ├── llm.py           # DeepSeek API wrapper
│   └── templates/       # Jinja2 templates
│
├── meta/
│   ├── manager.py       # MetadataManager class
│   └── als_parser.py    # ALS file parser
│
├── bronze/
│   └── loader.py        # SAS/CSV import
│
├── silver/
│   └── generator.py     # SQL generation
│
├── gold/
│   ├── engine.py        # Python script generation
│   └── stats.py         # Statistical functions
│
└── platinum/
    └── renderer.py      # Report rendering (stub)
```

## Future: prism-portal

The `archive/` directory contains an abandoned DuckDB-WASM implementation.

For a future interactive portal, consider:
- **Flask + Jinja2**: Server-side rendering
- **NiceGUI/Streamlit**: Python-native UI
- **Pre-generated JSON + vanilla JS**: No build step

Key feature: drill-down from Gold statistics to Silver raw data.

## Technology Stack

| Component | Technology |
|-----------|------------|
| Database | DuckDB |
| Language | Python 3.12 |
| Data Models | Pydantic v2 |
| Templates | Jinja2 |
| LLM | DeepSeek API |
| Stats | NumPy/Pandas (no scipy) |
