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
uv sync
```

### Running Tests
```bash
uv run pytest                  # Run all tests
uv run pytest tests/ -v        # Verbose output
uv run pytest -x               # Stop on first failure
```

### Linting and Formatting
```bash
uv run --extra dev black src/prism/                       # Format code
uv run --extra dev ruff check src/prism/                  # Lint code
uv run --extra dev mypy src/prism/                        # Type check
```

### Database Utilities
```bash
uv run duckdb <database>.duckdb               # Open DuckDB CLI
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

### Meta Schema (9 Tables)

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

**DDL Location**: Auto-generated from `src/prism/core/models.py` via `src/prism/meta/schema.py`

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
│   ├── core/                # Database, schema, config, models
│   ├── agent/               # LLM providers (zhipu, deepseek) + PydanticAI base
│   ├── meta/                # Metadata generation and management
│   │   ├── agent.py         # PydanticAI agent for meta generation
│   │   ├── generator.py     # Batch LLM generator
│   │   ├── extractor.py     # Mock shell extraction
│   │   ├── loader.py        # Load to meta tables
│   │   ├── excel_writer.py  # Excel output
│   │   ├── manager.py       # Metadata manager
│   │   └── als_parser.py    # ALS parsing
│   ├── bronze/              # Data loader
│   ├── silver/              # Silver transformation engine
│   ├── gold/                # Analysis engine
│   ├── platinum/            # Report renderer
│   └── transforms/          # Python transformations registry
├── tests/                   # Test files
├── examples/                # Example data
└── archive/                 # Deprecated code
```

---

## Meta Generation

The `prism.meta` module generates clinical trial metadata using a **two-step approach**:

### Step 1: Mock Shell → Meta Definitions

Use LLM to understand mock shell semantics and generate meta **definitions** (what variables are).

**Input:**
- Mock Shell (docx/xlsx)
- Footnotes, Programming notes

**Output:**
- Silver Variable Definitions (var_name, var_label, schema, data_type, description)
- Parameter Definitions
- Gold Statistic Definitions
- Platinum Deliverable Definitions

**Implementation:**
- `prism.meta.definitions.DefinitionAgent` - LLM-powered agent
- Does NOT require ALS
- Generates semantic definitions, not implementations

### Step 2: Meta Definitions → Derivations (Future)

Use LLM + ALS + SAP to generate **derivation rules** (how to transform data).

**Input:**
- Meta Definitions (from Step 1)
- ALS (raw field mappings)
- SAP (optional, with vector search)

**Output:**
- Bronze Dictionary (ALS structure)
- Derivation Rules (text format)
- Transformation Code (Polars)

**Implementation:**
- `prism.meta.derivations.DerivationAgent` - (Not yet implemented)

### LLM Providers

| Provider | Usage |
|----------|-------|
| DeepSeek (default) | `--provider deepseek` - Working, has balance |
| Zhipu | `--provider zhipu` - GLM-4 model (needs balance top-up) |

### CLI Commands

```bash
# Step 1: Generate meta definitions from mock shell
uv run prism meta generate --mock shell.docx -o meta.xlsx

# Generate for specific deliverables only
uv run prism meta generate --mock shell.docx -d "14.1.2.1,14.3.1" -o meta.xlsx

# Debug a single deliverable
uv run prism meta generate --mock shell.docx --debug 14.3.1 -v

# List deliverables without generating
uv run prism meta generate --mock shell.docx --list-only

# Load metadata to meta tables
uv run prism meta load --meta meta.xlsx --db study.duckdb

# Extract mock shell to JSON
uv run prism meta extract --mock shell.docx -o shell.json
```

### Module Structure

| Directory/File | Purpose |
|----------------|---------|
| `definitions/` | **Step 1**: Generate meta definitions from mock shell |
| `definitions/agent.py` | DefinitionAgent - LLM理解Mock Shell |
| `definitions/models.py` | MetaDefinitions, SilverVariableDefinition等 |
| `definitions/templates.py` | LLM prompt templates |
| `derivations/` | **Step 2**: Generate derivations (future) |
| `derivations/agent.py` | DerivationAgent - 生成转换规则 (NotImplemented) |
| `extractor.py` | Parse mock shell (docx/xlsx) to structured JSON |
| `loader.py` | Load metadata to meta tables |
| `excel_writer.py` | Formatted Excel output |
| `als_parser.py` | ALS parsing |

### Output Excel Sheets

| Sheet | Content |
|-------|---------|
| study_config | Population and visit definitions |
| params | Longitudinal parameter definitions |
| silver_variables | Silver layer variable specs (with **description** column) |
| platinum | Deliverable definitions |
| gold_statistics | Statistics definitions |
| review_needed | Items requiring human review |

---

## PydanticAI Architecture

PRISM uses PydanticAI for unified LLM-based generation across Meta, Silver, and Gold layers.

### Base Agent (`src/prism/agent/base.py`)
- Shared infrastructure for all agents
- Tool registry: ALS lookup, Bronze schema, Meta variables, Dependency check
- Provider abstraction: DeepSeek, Zhipu

### Shared Tools
| Tool | Purpose |
|------|---------|
| `lookup_als(domain, keywords)` | Look up ALS fields |
| `get_bronze_schema()` | Get Bronze layer tables/columns |
| `get_meta_variables(schema)` | Get variables from meta tables |
| `check_dependencies(var_names)` | Check if required variables exist |

---

## Key Dependencies

| Package | Purpose |
|---------|---------|
| duckdb | Database engine |
| pandas | Data manipulation |
| polars | Fast data processing (transforms) |
| pydantic | Schema validation |
| pydantic-ai | LLM agent framework |
| jinja2 | Templates |
| requests | HTTP (LLM API) |
| zhipuai | Zhipu LLM API |
| python-docx | Mock shell parsing |
| openpyxl | Excel reading/writing |

---

## Reference Documentation

- [README.md](README.md) - Project overview
- [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture design
