# AGENTS.md - Coding Agent Guidelines for PRISM-DB

This document provides guidelines for AI coding agents working in the PRISM-DB repository.

---

## Project Overview

PRISM-DB is a clinical trial data warehouse built on DuckDB implementing a three-layer Medallion architecture:
- **Bronze**: Raw EDC data imported from SAS/CSV/Excel
- **Silver**: Subject-level analysis-ready data (baseline, longitudinal, occurrence schemas)
- **Gold**: Group-level statistical aggregations

---

## Build, Test, and Lint Commands

### Setup
```bash
pip install -r requirements.txt
source .venv/bin/activate
```

### Running Tests
```bash
pytest                                    # Run all tests
pytest tests/test_phase1.py               # Run single test file
pytest tests/test_phase1.py::test_phase_1 # Run single test function
pytest -v                                 # Verbose output
pytest -x                                 # Stop on first failure
```

### Linting and Formatting
```bash
black src/prismdb/                        # Format code
black --check src/prismdb/                # Check formatting without changes
flake8 src/prismdb/                       # Lint code
mypy src/prismdb/                         # Type check
```

### Database Utilities
```bash
duckdb <database>.duckdb                  # Open DuckDB CLI
```

---

## Code Style Guidelines

### Python Version
- Target **Python 3.12**
- Use modern Python features (type hints, f-strings, dataclasses where appropriate)

### Imports
```python
# Order: standard library → third-party → local
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

import duckdb
import pandas as pd
import numpy as np

from .database import Database
```

### Naming Conventions
| Type | Convention | Example |
|------|------------|---------|
| Modules | snake_case | `parse_als_v2.py`, `init_bronze.py` |
| Classes | PascalCase | `Database`, `MetadataManager` |
| Functions | snake_case | `parse_als_to_db()`, `load_study_data()` |
| Variables | snake_case | `db_path`, `study_code` |
| Constants | UPPER_SNAKE | `MAX_RETRIES` |
| SQL schemas/tables | lowercase | `bronze.demog`, `meta.variables` |

### Type Hints
```python
def query_df(self, sql: str, params: Optional[tuple] = None) -> Any:
    ...

def get_variables(self, schema: str = None, block: str = None) -> List[Dict]:
    ...
```

### Docstrings
```python
def execute(self, sql: str, params: Optional[tuple] = None) -> duckdb.DuckDBPyConnection:
    """
    Execute SQL statement.
    
    Args:
        sql: SQL statement
        params: Optional parameters
        
    Returns:
        DuckDB connection object
    """
```

### Logging
```python
import logging

logger = logging.getLogger(__name__)

logger.info(f"Connected to database: {db_path}")
logger.warning(f"Missing codelist: {codelist_name}")
logger.error(f"Failed to parse file: {error}")
```

### Error Handling
```python
try:
    entries_df = pd.read_excel(als_path, sheet_name='DataDictionaryEntries')
except Exception:
    return {}
```

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
| `meta.outputs` | Output definitions (table/listing/figure) |
| `meta.output_variables` | Output-variable associations |
| `meta.output_params` | Output-parameter associations |
| `meta.functions` | Complex function library |
| `meta.dependencies` | Variable dependency graph |

**DDL Location**: `sql/init_meta.sql`
**Python Models**: `src/prismdb/schema/models.py`

### Data Layer Conventions
| Layer | Schema Pattern | Row Granularity |
|-------|----------------|-----------------|
| Bronze | `bronze.<form_name>` | Raw EDC records |
| Silver | `silver.baseline`, `silver.longitudinal`, `silver.occurrence` | Subject-level |
| Gold | `gold.baseline`, `gold.longitudinal`, `gold.occurrence` | Group-level |

### JSON Storage in SQL
Store structured data as JSON in TEXT columns:
```python
source_vars_json = json.dumps(source_vars) if source_vars else None
sql = "INSERT INTO meta.derivations (..., source_vars) VALUES (..., ?)"
db.execute(sql, (..., source_vars_json))
```

---

## Testing Conventions

### Test File Structure
```python
"""
Test Script for Phase X.X
Brief description of what is being tested
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from prismdb import Database, init_database

def test_feature():
    """Test description"""
    db_path = "test_temp.duckdb"
    sql_script = str(Path(__file__).parent.parent / 'sql' / 'init_meta.sql')
    
    db = init_database(db_path, sql_script)
    
    result = db.query_df("SELECT * FROM meta.variables")
    assert len(result) >= 0
    
    db.close()
```

### Test Database Naming
- Use descriptive names: `test_phase1_v31.duckdb`, `test_als_v31.duckdb`
- Clean up test databases when appropriate

---

## SQL Conventions

### Schema Creation
```sql
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE TABLE IF NOT EXISTS bronze.demog (...);
```

### Metadata Tables
Always include timestamps:
```sql
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

### JSON Columns
Store arrays/objects as JSON TEXT:
```sql
source_vars TEXT,     -- JSON array
render_options TEXT,  -- JSON object
input_params TEXT,    -- JSON object
```

---

## Hard Rules

1. **No Change-Note Comments**: Never add comments describing changes (e.g., "removed", "cleanup", "hotfix")
2. **No Unnecessary Comments**: Only comment non-obvious logic
3. **Remove Dead Code**: Delete unused imports, functions, and variables
4. **Minimal Diffs**: Make targeted changes without unrelated modifications
5. **Ask for Clarification**: When requirements are ambiguous, ask before proceeding

---

## File Organization

```
prism-db/
├── src/prismdb/           # Main source code
│   ├── schema/            # Pydantic models for meta tables
│   │   ├── __init__.py
│   │   └── models.py
│   ├── database.py        # Database connection
│   ├── metadata.py        # Metadata CRUD operations
│   ├── parse_als_v2.py    # ALS parser
│   └── init_bronze.py     # Bronze data import
├── sql/                   # SQL scripts
│   └── init_meta.sql      # Meta schema DDL (11 tables)
├── tests/                 # Test files
├── docs/                  # Documentation
├── examples/              # Example data and outputs
└── requirements.txt       # Dependencies
```

---

## Key Dependencies

| Package | Purpose |
|---------|---------|
| duckdb | Database engine |
| pandas | Data manipulation |
| openpyxl | Excel handling |
| pydantic | Schema validation |
| pytest | Testing |
| black | Code formatting |
| flake8 | Linting |
| mypy | Type checking |

---

## Reference Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - Complete architecture design (v3.1)
- [docs/META_SCHEMA.md](docs/META_SCHEMA.md) - Meta schema detailed design
- [README.md](README.md) - Project overview
