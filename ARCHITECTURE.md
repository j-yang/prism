# PRISM Architecture

## Overview

PRISM is a clinical trial data warehouse built on DuckDB with AI-powered code generation.

## Medallion Architecture

```
                    ┌─────────────────────────────────────┐
                    │                  Meta Layer                  │
                    │  10 tables: params, attrs, visits,          │
                    │  bronze_dictionary, silver_dictionary,        │
                    │  gold_dictionary, platinum_dictionary,        │
                    │  form_classification, dependencies, etc.                │
                    └──────────────────────┬──────────────────────┘
                                           │
                    ┌──────────────────────▼──────────────────────┐
                    │                Bronze Layer                  │
                    │  Raw EDC data imported from SAS/CSV/Excel    │
                    │  3 tables: bronze_baseline,                │
                    │            bronze_longitudinal,             │
                    │            bronze_occurrence                    │
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

## Meta Schema (10 Tables)

### Study Configuration
| Table | Purpose |
|-------|---------|
| `meta.study_info` | Study基本信息 |
| `meta.visits` | Analysis visit definitions |
| `meta.form_classification` | Form → Domain/Schema 映射 |

### Parameter & Attribute Definitions
| Table | Purpose |
|-------|---------|
| `meta.params` | Longitudinal参数定义 (可外链) |
| `meta.attrs` | Occurrence domain扩展字段定义 |

### Data Dictionaries
| Table | Purpose |
|-------|---------|
| `meta.bronze_dictionary` | Bronze层数据字典 (来自ALS解析) |
| `meta.silver_dictionary` | Silver层数据字典 (衍生变量) |
| `meta.gold_dictionary` | Gold层数据字典 (Group Level统计定义) |

### Deliverable Definitions
| Table | Purpose |
|-------|---------|
| `meta.platinum_dictionary` | Platinum交付物定义 (table/figure/listing) |

### Dependencies
| Table | Purpose |
|-------|---------|
| `meta.dependencies` | 变量依赖关系 |

## Gold Layer Design

### Gold Schema (3 Tables)

| Table | Purpose |
|-------|---------|
| `gold.baseline` | Group-level baseline statistics |
| `gold.longitudinal` | Group-level longitudinal statistics |
| `gold.occurrence` | Group-level occurrence statistics |

### Gold Table Structure

每行 = 一个 group + 一个 element + 一个 selection + 统计量JSON

```sql
-- gold.baseline
deliverable_id, element_id, group_id, statistics(JSON)

-- gold.longitudinal  
deliverable_id, element_id, group_id, visit, statistics(JSON)

-- gold.occurrence
deliverable_id, element_id, group_id, selection, statistics(JSON)
```

示例数据：
```json
// gold.baseline - 连续变量
{"n": 50, "mean": 45.2, "sd": 12.3, "median": 44.0}

// gold.baseline - 分类变量
{"n": 30, "pct": 60.0}

// gold.occurrence - 事件统计
{"n_subjects": 10, "n_events": 15, "pct": 20.0}
```

### Gold Dictionary Schema

```sql
CREATE TABLE meta.gold_dictionary (
    element_id TEXT NOT NULL,          -- 变量名/paramcd/coding_high/coding_low
    group_id TEXT NOT NULL,            -- 分组值：Drug, Placebo
    schema TEXT NOT NULL,              -- baseline, longitudinal, occurrence

    population TEXT,                   -- SAFFL, FASFL
    selection TEXT,                    -- 过滤条件
                                      -- baseline: NULL
                                      -- longitudinal: "visit=VISIT1"
                                      -- occurrence: "domain=AE;saefl=Y"

    statistics JSON,                   -- 要计算的统计量 ["n", "mean", "sd"]

    deliverable_id TEXT,               -- 关联的 platinum 交付物

    description TEXT,
    unit TEXT,
    display_order INTEGER,
    created_at TIMESTAMP,

    PRIMARY KEY (element_id, group_id, schema, COALESCE(selection, ''))
);
```

## Platinum Layer Design

### Platinum Dictionary Schema

```sql
CREATE TABLE meta.platinum_dictionary (
    deliverable_id TEXT PRIMARY KEY,    -- "T1_DEMOG", "L2_AE"
    deliverable_type TEXT NOT NULL,    -- table, listing, figure

    title TEXT,

    schema TEXT,                       -- baseline, longitudinal, occurrence

    elements JSON,                     -- 引用的元素
    -- [{"type": "variable", "id": "age", "label": "Age (Years)"},
    --  {"type": "param", "id": "PHGA", "label": "Physician Global Assessment"},
    --  {"type": "attr", "id": "saefl", "filter": "saefl='Y'"}]

    population TEXT,

    section TEXT,
    display_order INTEGER,

    created_at TIMESTAMP
);
```

## Agent System

### Code Generation Flow

```
meta.silver_dictionary (transformation) ──▶ Template Match? ──▶ Yes ──▶ Jinja2 Template
                                                 │
                                                 No
                                                 │
                                                 ▼
                                    DeepSeek LLM ──▶ Generated SQL/Python
                                                 │
                                                 ▼
                                    Needs Review (flagged )
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
| age_group | "Age categorization" | `CASE WHEN age < 18 THEN '<18' ...` |
| concat | "Column concatenation" | `CONCAT(a, b, c)` |
| change_baseline | "Baseline change" | `value - baseline_value` |

## Data Flow

```
1. Parse ALS
   parse_als_to_db() → meta.bronze_dictionary, meta.form_classification,
                       meta.visits, bronze DDL

2. Load Raw Data
   load_sas_to_bronze() → bronze.* tables

3. Define Silver Variables (from Spec)
   meta.silver_dictionary ← derivation rules

4. Generate Silver SQL
   SilverGenerator.generate_all() → derive_baseline.sql, etc.

5. Execute Silver SQL
   User runs generated SQL → silver.* tables

6. Define Gold Statistics (from Spec)
   meta.gold_dictionary ← group-level analysis definitions

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
│   ├── schema.py        # Pydantic models (BronzeVariable, SilverVariable, GoldVariable, PlatinumDeliverable, ...)
│   └── config.py        # Path helpers
│
├── sql/
│   ├── init_meta.sql    # Meta schema DDL (v5.1)
│   ├── init_bronze.sql  # Bronze schema DDL
│   ├── init_silver.sql  # Silver schema DDL
│   ├── init_gold.sql    # Gold schema DDL
│   └── init_traceability.sql
│
├── agent/
│   ├── llm.py           # DeepSeek API wrapper
│   └── templates/       # Jinja2 templates
│
├── meta/
│   ├── manager.py       # MetadataManager class (CRUD for all dictionary tables)
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

## Traceability Schema (2 Tables)

| Table | Purpose |
|-------|---------|
| `meta.data_lineage` | Gold → Silver 追溯 |
| `meta.silver_sources` | Silver → Bronze 追溯 |

### Helper View
| View | Purpose |
|------|---------|
| `meta.v_full_lineage` | 完整追溯链 (Gold → Silver → Bronze) |

## Technology Stack

| Component | Technology |
|-----------|------------|
| Database | DuckDB |
| Language | Python 3.12 |
| Data Models | Pydantic v2 |
| Templates | Jinja2 |
| LLM | DeepSeek API |
| Stats | NumPy/Pandas |
