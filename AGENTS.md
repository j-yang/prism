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
| SQL schemas/tables | lowercase | `bronze.demog`, `meta.variables` |

---

## Architecture Patterns

### Database Connections
Use context managers for database connections:
```python
with Database(db_path) as db:
    result = db.query_df("SELECT * FROM bronze.demog")
```

### Meta Schema (11 Tables)

All metadata is stored in the `meta` schema:

**Reference Tables (可外链)**:
| Table | Purpose |
|-------|---------|
| `meta.params` | Longitudinal parameter definitions |
| `meta.flags` | Occurrence event flag definitions |
| `meta.visits` | Analysis visit definitions |

**Study-Specific Tables**:
| Table | Purpose |
|-------|---------|
| `meta.study_info` | Current study information |
| `meta.variables` | Unified variable registry |
| `meta.derivations` | Transformation rules |
| `meta.outputs` | Output definitions |
| `meta.output_variables` | Output-variable associations |
| `meta.output_params` | Output-parameter associations |
| `meta.functions` | Complex function library |
| `meta.dependencies` | Variable dependency graph |

**DDL Location**: `src/prism/sql/init_meta.sql`

### Data Layer Conventions
| Layer | Schema Pattern | Row Granularity |
|-------|----------------|-----------------|
| Bronze | `bronze.<form_name>` | Raw EDC records |
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
│   ├── bronze/              # Data loader
│   ├── silver/              # SQL generator
│   ├── gold/                # Analysis engine
│   └── platinum/            # Report renderer
├── tests/                   # Test files
├── examples/                # Example data
└── archive/                 # Deprecated code
```

---

## Key Dependencies

| Package | Purpose |
|---------|---------|
| duckdb | Database engine |
| pandas | Data manipulation |
| pydantic | Schema validation |
| jinja2 | Templates |
| requests | HTTP (LLM API) |

---

## Reference Documentation

- [README.md](README.md) - Project overview
- [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture design
