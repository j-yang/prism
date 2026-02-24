# AGENTS.md - Coding Agent Guidelines for PRISM

This document provides guidelines for AI coding agents working in the PRISM repository.

---

## Project Overview

PRISM is a clinical trial data warehouse built on DuckDB implementing a Medallion architecture:
- **Bronze**: Raw EDC data imported from SAS/CSV/Excel
- **Silver**: Subject-level analysis-ready data (baseline, longitudinal, occurrence schemas)
- **Gold**: Group-level statistical aggregations
- **Platinum**: Report rendering (RTF/PDF/HTML)

---

## Build, Test, and Lint Commands

### Setup
```bash
pip install -e .
```

### Running Tests
```bash
PYTHONPATH=src pytest                  # Run all tests
PYTHONPATH=src pytest tests/ -v        # Verbose output
PYTHONPATH=src pytest -x               # Stop on first failure
```

### Linting and Formatting
```bash
black src/prism/                       # Format code
ruff check src/prism/                  # Lint code
mypy src/prism/                        # Type check
```

### Database Utilities
```bash
duckdb <database>.duckdb               # Open DuckDB CLI
```

---

## Code Style Guidelines

### Python Version
- Target **Python 3.12**
- Use modern Python features (type hints, f-strings)

### Imports
```python
# Order: standard library → third-party → local
from typing import Dict, List, Optional

import duckdb
import pandas as pd

from prism.core.database import Database
```

### Naming Conventions
| Type | Convention | Example |
|------|------------|---------|
| Modules | snake_case | `als_parser.py`, `loader.py` |
| Classes | PascalCase | `Database`, `MetadataManager` |
| Functions | snake_case | `parse_als_to_db()`, `load_study_data()` |
| Variables | snake_case | `db_path`, `study_code` |
| SQL schemas/tables | lowercase | `bronze.baseline`, `meta.gold_dictionary` |

---

## Architecture Patterns

### Database Connections
Use context managers for database connections:
```python
with Database(db_path) as db:
    result = db.query_df("SELECT * FROM bronze.demog")
```

### Meta Schema (10 Tables)

All metadata is stored in the `meta` schema:

**Study Configuration**:
| Table | Purpose |
|-------|---------|
| `meta.study_info` | Study基本信息 |
| `meta.visits` | Analysis visit definitions |
| `meta.form_classification` | Form → Domain/Schema 映射 |

**Parameter & Attribute Definitions**:
| Table | Purpose |
|-------|---------|
| `meta.params` | Longitudinal参数定义 (可外链) |
| `meta.attrs` | Occurrence domain扩展字段定义 |

**Data Dictionaries**:
| Table | Purpose |
|-------|---------|
| `meta.bronze_dictionary` | Bronze层数据字典 (来自ALS解析) |
| `meta.silver_dictionary` | Silver层数据字典 (衍生变量) |
| `meta.gold_dictionary` | Gold层数据字典 (Group Level统计定义) |

**Deliverable Definitions**:
| Table | Purpose |
|-------|---------|
| `meta.platinum_dictionary` | Platinum交付物定义 (table/figure/listing) |

**Dependencies**:
| Table | Purpose |
|-------|---------|
| `meta.dependencies` | 变量依赖关系 |

**DDL Location**: `src/prism/sql/init_meta.sql`

### Data Layer Conventions
| Layer | Schema Pattern | Row Granularity |
|-------|----------------|-----------------|
| Bronze | `bronze.baseline`, `bronze.longitudinal`, `bronze.occurrence` | Raw EDC records |
| Silver | `silver.baseline`, `silver.longitudinal`, `silver.occurrence` | Subject-level |
| Gold | `gold.baseline`, `gold.longitudinal`, `gold.occurrence` | Group-level |

---

## Hard Rules

1. **No Change-Note Comments**: Never add comments describing changes
2. **No Unnecessary Comments**: Only comment non-obvious logic
3. **Remove Dead Code**: Delete unused imports, functions, and variables
4. **Minimal Diffs**: Make targeted changes without unrelated modifications
5. **Ask for Clarification**: When requirements are ambiguous, ask before proceeding

---

## File Organization

```
prism/
├── src/prism/               # Main source code
│   ├── core/                # Database, schema, config
│   ├── sql/                 # DDL scripts
│   ├── agent/               # LLM, templates
│   ├── meta/                # Metadata manager, ALS parser
│   ├── spec/                # Spec Agent (mock shell → spec)
│   ├── bronze/              # Data loader
│   ├── silver/              # SQL generator
│   ├── gold/                # Analysis engine
│   └── platinum/            # Report renderer
├── tests/                   # Test files
├── examples/                # Example data
└── archive/                 # Deprecated code
```

---

## Spec Agent

The `prism.spec` module generates clinical trial specs from mock shell documents.

### CLI Commands
```bash
prism spec generate --mock shell.docx --als als.xlsx --output spec.xlsx
prism spec learn --original draft.json --corrected final.json --study STUDY001
prism spec patterns stats
```

### Module Structure
| File | Purpose |
|------|---------|
| `extractor.py` | Parse mock shell (docx/xlsx) to structured JSON |
| `generator.py` | Generate silver/gold specs via LLM |
| `matcher.py` | Match variables to ALS fields |
| `learner.py` | Learn from human corrections |
| `memory.py` | DuckDB pattern storage |
| `excel_writer.py` | Formatted Excel output |
| `cli.py` | Command-line interface |

### Memory Store
- Location: `~/.prism/memory.duckdb`
- Stores learned patterns for cross-study learning
- Tables: `patterns`, `variable_mappings`, `study_history`

---

## Key Dependencies

| Package | Purpose |
|---------|---------|
| duckdb | Database engine |
| pandas | Data manipulation |
| pydantic | Schema validation |
| jinja2 | Templates |
| requests | HTTP (LLM API) |
| python-docx | Mock shell parsing |
| openpyxl | Excel reading/writing |

---

## Reference Documentation

- [README.md](README.md) - Project overview
- [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture design
