# PRISM Architecture

## Overview

PRISM is a clinical trial data warehouse built on DuckDB with unified PydanticAI agents for code generation.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     meta (Specification)                    │
│  9 tables: study_info, visits, form_classification,        │
│  bronze_dictionary, params, attrs, silver_dictionary,       │
│  gold_dictionary, platinum_dictionary, dependencies         │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    Bronze (Raw Data)                        │
│  One table per form: bronze.ae, bronze.cm, bronze.dm, ...   │
│  Minimal processing: lowercase columns, date conversion     │
└──────────────────────────┬──────────────────────────────────┘
                           │ PydanticAI Silver Agent
┌──────────────────────────▼──────────────────────────────────┐
│                    Silver (Derived)                         │
│  3 schemas: silver.baseline, silver.longitudinal,           │
│             silver.occurrence                               │
│  Output: Python Polars code (human reviews before run)      │
└──────────────────────────┬──────────────────────────────────┘
                           │ PydanticAI Gold Agent
┌──────────────────────────▼──────────────────────────────────┐
│                    Gold (Statistics)                        │
│  3 schemas: gold.baseline, gold.longitudinal,               │
│             gold.occurrence                                 │
│  Output: Python Polars code (human reviews before run)      │
└──────────────────────────┬──────────────────────────────────┘
                           │ PydanticAI Platinum Agent
┌──────────────────────────▼──────────────────────────────────┐
│                   Platinum (Deliverables)                   │
│  Output: PowerPoint slide decks (native charts, editable)   │
└─────────────────────────────────────────────────────────────┘
```

---

## PydanticAI Unified Architecture

All layers use the same PydanticAI agent pattern:

```
┌─────────────────────────────────────────────────────────────┐
│                    BaseAgent (agent/base.py)                │
│  - Provider abstraction (DeepSeek, Zhipu)                   │
│  - Tool registry (ALS lookup, Meta variables, Deps check)  │
│  - Structured output via Pydantic models                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
       ┌───────────────────┼───────────────────┐
       │                   │                   │
┌──────▼──────┐     ┌──────▼──────┐     ┌──────▼──────┐
│  MetaAgent  │     │SilverAgent  │     │ PlatinumAgent│
│ (10 vars/   │     │(Polars code)│     │(Slide decks) │
│  batch)     │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
```

### Shared Tools

| Tool | Purpose |
|------|---------|
| `lookup_als(domain, keywords)` | Look up ALS fields for a domain |
| `get_bronze_schema()` | Get Bronze layer tables/columns |
| `get_meta_variables(schema)` | Get variables from meta tables |
| `check_dependencies(var_names)` | Check if required variables exist |

---

## Meta Schema (9 Tables)

### Study Configuration
| Table | Purpose |
|-------|---------|
| `meta.study_info` | Study basic information |
| `meta.visits` | Analysis visit definitions |
| `meta.form_classification` | Form → Domain/Schema mapping |

### Data Dictionary
| Table | Purpose |
|-------|---------|
| `meta.bronze_dictionary` | Bronze layer data dictionary (from ALS) |
| `meta.silver_dictionary` | Silver layer data dictionary (from Meta) |
| `meta.gold_dictionary` | Gold layer statistics definitions |
| `meta.platinum_dictionary` | Platinum deliverable definitions |

### Definitions
| Table | Purpose |
|-------|---------|
| `meta.params` | Longitudinal parameter definitions |
| `meta.attrs` | Occurrence extended field definitions |
| `meta.dependencies` | Variable dependency relationships |

---

## Bronze Layer

### Design Principle

**Store by original Form, maintain full Traceability**

```sql
bronze.ae    -- Adverse Events
bronze.cm    -- Concomitant Medications
bronze.dm    -- Demographics
bronze.lb    -- Laboratory
bronze.vs    -- Vital Signs
... (N tables, one per form)
```

### Processing Rules

1. Column names: lowercase
2. Date conversion: SAS date → DATE type
3. Keep all fields: no filtering by default

---

## Silver Layer

3 schemas with consistent structure:

### baseline
- One row per subject
- Derived from baseline forms

### longitudinal
- One row per subject per visit
- Derived from longitudinal forms

### occurrence
- One row per event
- Consolidated from AE, CM, MH, PR forms

### Generation Workflow

```bash
# 1. Generate Polars code
uv run prism silver generate --schema baseline --db study.duckdb -o generated/silver/

# 2. Review generated code
cat generated/silver/baseline.py

# 3. Run after review
uv run python generated/silver/baseline.py
```

---

## Gold Layer

3 schemas for statistical aggregations:

| Schema | Purpose |
|--------|---------|
| `gold.baseline` | Group-level baseline statistics |
| `gold.longitudinal` | Group-level longitudinal statistics |
| `gold.occurrence` | Group-level occurrence statistics |

### Generation Workflow

```bash
# 1. Generate Polars code
uv run prism gold generate --schema baseline --db study.duckdb -o generated/gold/

# 2. Review generated code
cat generated/gold/baseline.py

# 3. Run after review
uv run python generated/gold/baseline.py
```

---

## Platinum Layer

### PowerPoint Generation

```bash
# Generate slide deck from all deliverables
uv run prism platinum generate --db study.duckdb -o report.pptx
```

### Features

| Feature | Description |
|---------|-------------|
| Title slides | Study title, protocol number |
| Table slides | Demographics, efficacy, safety |
| Figure slides | Native PPTX charts (line, bar, scatter) |
| Listing slides | Data listings |
| Combined output | All slides in one PPTX file |

---

## File Organization

```
src/prism/
├── core/
│   ├── database.py      # DuckDB connection wrapper
│   ├── models.py        # Pydantic models (single source of truth)
│   └── schema.py        # Auto-generated DDL from Pydantic
│
├── agent/
│   ├── base.py          # PydanticAI base agent + tools
│   ├── provider.py      # LLM provider interface
│   ├── deepseek.py      # DeepSeek implementation
│   └── zhipu.py         # Zhipu implementation
│
├── meta/
│   ├── agent.py         # PydanticAI agent for meta generation
│   ├── generator.py     # Batch LLM generator
│   ├── extractor.py     # Mock shell extraction
│   ├── loader.py        # Load to meta tables
│   ├── excel_writer.py  # Excel output
│   ├── manager.py       # Metadata manager
│   └── als_parser.py    # ALS parsing
│
├── silver/
│   ├── agent.py         # PydanticAI agent for Silver
│   ├── cli.py           # CLI commands
│   └── engine.py        # Transformation engine
│
├── gold/
│   ├── agent.py         # PydanticAI agent for Gold
│   ├── cli.py           # CLI commands
│   ├── engine.py        # Statistics engine
│   └── stats.py         # Statistical functions
│
├── platinum/
│   ├── agent.py         # PydanticAI agent for Platinum
│   ├── cli.py           # CLI commands
│   ├── renderer.py      # PPTX renderer (python-pptx)
│   ├── charts.py        # Native chart helpers
│   └── templates.py     # Slide layout constants
│
├── bronze/
│   └── loader.py        # SAS/CSV/Excel import
│
└── transforms/
    ├── registry.py      # Transform registration
    ├── silver/          # Silver transformation files
    └── gold/            # Gold transformation files
```

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| Database | DuckDB |
| Language | Python 3.12 |
| Data Models | Pydantic v2 |
| LLM Agent | pydantic-ai |
| LLM Provider | DeepSeek, Zhipu |
| Data Processing | Polars |
| Slide Generation | python-pptx |
| Templates | Jinja2 |
| Package Manager | uv |

---

## Data Flow

```
1. ALS Parsing
   parse_als_to_db() → bronze tables, meta.bronze_dictionary

2. Meta Generation
   prism meta generate → meta.xlsx (silver_variables, params, etc.)
   prism meta load → meta.* tables

3. Silver Generation
   SilverAgent → generated/silver/*.py (Polars code)
   Human reviews → Run code → silver.* tables

4. Gold Generation
   GoldAgent → generated/gold/*.py (Polars code)
   Human reviews → Run code → gold.* tables

5. Platinum Generation
   PlatinumAgent → report.pptx (slide deck)
```
