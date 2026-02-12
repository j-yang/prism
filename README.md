# PRISM-DB

**Pooled Research Intelligence & Statistical Mapping - Database**

Clinical trial data warehouse built on DuckDB for multi-study analysis.

---

## Overview

PRISM-DB is a database-centric framework for managing clinical trial data across multiple studies. It implements a three-layer Medallion architecture (Bronze → Silver → Gold) to transform raw EDC data into analysis-ready statistical datasets.

**Project Scope**:
- ✅ Database architecture and schema management
- ✅ ETL pipelines (Bronze → Silver → Gold)
- ✅ Statistical computation and aggregation
- ❌ Rendering/output generation (handled by separate systems)
- ❌ AI Agent integration (future roadmap)

**Key Features**:
- **Multi-study support**: Centralized data model for cross-study analysis
- **Medallion architecture**: Bronze (Raw) → Silver (Subject-level) → Gold (Group-level)
- **DuckDB powered**: Fast analytical queries, zero-copy R/Python integration
- **Metadata-driven**: Schema, derivations, and outputs defined in metadata tables
- **Three data patterns**: baseline, longitudinal, occurrence

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  study.duckdb                           │
├─────────────────────────────────────────────────────────┤
│  Bronze Layer (Raw EDC data)                            │
│  ├─ bronze.demog, bronze.vs, bronze.ae, ...            │
│                       ↓                                 │
│  Silver Layer (Subject-level, analysis-ready)           │
│  ├─ silver.baseline      (1 row/subject)               │
│  ├─ silver.longitudinal  (1 row/subj×param×visit)      │
│  ├─ silver.occurrence    (1 row/event)                 │
│                       ↓                                 │
│  Gold Layer (Group-level statistics, long tables)       │
│  ├─ gold.baseline        (aggregated by treatment)     │
│  ├─ gold.longitudinal    (aggregated by visit)         │
│  ├─ gold.occurrence      (aggregated by category)      │
│                       ↓                                 │
│  Metadata Schema                                        │
│  ├─ meta.schema_docs    (table structures)             │
│  ├─ meta.data_catalog   (variable registry)            │
│  ├─ meta.output_spec    (output definitions)           │
│  ├─ meta.derivations    (transformation rules)         │
│  └─ meta.output_assembly (assembly instructions)       │
└─────────────────────────────────────────────────────────┘
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design.

---

## Project Structure

```
prism-db/
├── prismdb/                  # Core Python modules
│   ├── __init__.py
│   ├── parse_als.py          # ALS parser (EDC schema)
│   ├── init_bronze.py        # Bronze layer initialization
│   ├── derive_silver.py      # Silver layer derivation engine
│   ├── compute_gold.py       # Gold layer statistical computation
│   ├── metadata.py           # Metadata management
│   └── utils.py              # Utilities
│
├── sql/                      # SQL templates and scripts
│   ├── init_metadata.sql     # Create metadata tables
│   ├── templates/            # Derivation SQL templates
│   │   ├── baseline.sql
│   │   ├── longitudinal.sql
│   │   └── occurrence.sql
│   └── examples/             # Example queries
│
├── rule_docs/                # Complex derivation documentation
│   ├── mmt8.md               # MMT8 composite score
│   ├── haqdi.md              # HAQ-DI scoring
│   └── ...
│
├── studies/                  # Study-specific data and specs
│   └── D8318N00001/
│       ├── D8318N00001_ALS.xlsx   # EDC schema
│       ├── study.duckdb           # DuckDB database
│       ├── derivations.xlsx       # Derivation spec
│       ├── output_spec.xlsx       # Output definitions
│       └── logs/                  # Execution logs
│
├── tests/                    # Unit tests
│   ├── test_parse_als.py
│   ├── test_derive_silver.py
│   └── test_compute_gold.py
│
├── docs/                     # Documentation
│   ├── ARCHITECTURE.md       # Architecture design
│   ├── DATABASE_SCHEMA.md    # Database schema reference
│   └── USER_GUIDE.md         # Usage guide
│
├── ARCHITECTURE.md           # Main architecture doc (symlink)
├── PROJECT_PLAN.md           # Implementation plan
├── README.md                 # This file
└── requirements.txt          # Python dependencies
```

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Key dependencies**:
- `duckdb` - Database engine
- `pandas` - Data manipulation
- `openpyxl` - Excel file handling
- `pyyaml` - Configuration

### 2. Initialize Study Database

```python
from prismdb import init_database, parse_als

# Parse ALS and create Bronze schema
parse_als(
    als_path="studies/D8318N00001/D8318N00001_ALS.xlsx",
    db_path="studies/D8318N00001/study.duckdb",
    study_code="D8318N00001"
)

# Initialize metadata tables
init_database(db_path="studies/D8318N00001/study.duckdb")
```

### 3. Load Raw Data to Bronze

```python
from prismdb import load_bronze

# Import CSV/Excel raw data
load_bronze(
    raw_data_path="studies/D8318N00001/raw/",
    db_path="studies/D8318N00001/study.duckdb"
)
```

### 4. Execute Derivations → Silver

```python
from prismdb import derive_silver

# Execute derivations based on meta.derivations
derive_silver(
    db_path="studies/D8318N00001/study.duckdb",
    study_code="D8318N00001"
)
```

### 5. Compute Statistics → Gold

```python
from prismdb import compute_gold

# Generate Gold layer statistics
compute_gold(
    db_path="studies/D8318N00001/study.duckdb",
    output_spec="studies/D8318N00001/output_spec.xlsx"
)
```

### 6. Query Results

```python
import duckdb

con = duckdb.connect("studies/D8318N00001/study.duckdb")

# Query Gold layer for demographics table
demog = con.execute("""
    SELECT * FROM gold.baseline
    WHERE output_id = 'T1_demog'
    ORDER BY group1_value, row_order
""").df()

print(demog)
```

---

## Data Layers

### Bronze Layer
- **Purpose**: Store raw EDC data as-is
- **Source**: Direct import from CSV/SAS/Excel
- **Structure**: Preserves original form structure
- **Tables**: `bronze.demog`, `bronze.vs`, `bronze.ae`, etc.

### Silver Layer
- **Purpose**: Analysis-ready subject-level data
- **Source**: Derived from Bronze via `meta.derivations`
- **Structure**: Organized into three schemas
  - `silver.baseline`: 1 row per subject (demographics, baseline)
  - `silver.longitudinal`: 1 row per subject × param × visit (labs, vitals, efficacy)
  - `silver.occurrence`: 1 row per event (AE, CM, MH)

### Gold Layer
- **Purpose**: Group-level statistical aggregations
- **Source**: Computed from Silver via `meta.output_spec`
- **Structure**: Long tables with multi-dimensional grouping
  - `gold.baseline`: Baseline stats by treatment group
  - `gold.longitudinal`: Longitudinal stats by visit
  - `gold.occurrence`: Event stats by category

**Gold Table Schema** (unified long-table design):
```sql
CREATE TABLE gold.baseline (
    output_id TEXT,        -- Links to meta.output_spec
    group1_name TEXT,      -- Primary grouping (e.g., 'TRTA')
    group1_value TEXT,     -- Group value (e.g., 'Drug A')
    group2_name TEXT,      -- Secondary grouping (e.g., 'SEX')
    group2_value TEXT,     -- Subgroup value (e.g., 'Male')
    comparison TEXT,       -- For hypothesis testing
    variable TEXT,         -- Variable name
    category TEXT,         -- Category for categorical vars
    stat_name TEXT,        -- Statistic type (n, mean, pct, p_value)
    stat_value REAL,       -- Numeric value
    stat_display TEXT,     -- Formatted display value
    row_order INTEGER      -- Display order
);
```

---

## Metadata Tables

All metadata is stored in the `meta` schema:

| Table | Purpose |
|-------|---------|
| `meta.schema_docs` | Database schema documentation |
| `meta.data_catalog` | Variable registry |
| `meta.derivations` | Transformation rules (Bronze → Silver) |
| `meta.output_spec` | Output definitions (Silver → Gold) |
| `meta.output_assembly` | Assembly instructions for rendering |

---

## Workflow

```
1. Parse ALS → Generate bronze.* tables + meta.schema_docs
2. Load raw data → Populate bronze.* tables
3. Define derivations → meta.derivations (manual/AI-assisted)
4. Execute derivations → Generate silver.* tables
5. Define outputs → meta.output_spec (manual)
6. Compute statistics → Generate gold.* tables
7. Export data → Query gold.* for downstream use
```

---

## Development Status

**Current Phase**: Phase 1 - Database Framework (In Progress)

- [x] Architecture design v3.0
- [x] ALS parser basic functionality
- [x] Form classification logic
- [ ] DuckDB migration
- [ ] Metadata tables implementation
- [ ] Bronze layer initialization
- [ ] Silver derivation engine
- [ ] Gold computation engine

See [PROJECT_PLAN.md](PROJECT_PLAN.md) for detailed roadmap.

---

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - Complete architecture design
- [PROJECT_PLAN.md](PROJECT_PLAN.md) - Implementation plan and timeline
- [docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md) - Detailed schema reference
- [docs/USER_GUIDE.md](docs/USER_GUIDE.md) - User guide and best practices

---

## Future Roadmap

### Phase 2: Advanced Features
- Multi-study shared metadata
- Complex statistical models (MMRM, Cox)
- Incremental updates
- Data lineage tracking

### Phase 3: Ecosystem Integration
- R package (`prismdb` for R)
- Python package (`prism-db` on PyPI)
- CLI tools
- CI/CD integration

### Separate Projects (Out of Scope)
- **prism-render**: Rendering engine for PPT/RTF/PDF
- **prism-agent**: AI agent for code generation

---

## Contributing

This is currently an internal project. Collaboration guidelines will be added when the project is ready for external contributors.

---

## License

[To be determined]