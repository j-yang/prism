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

PRISM uses OpenCode Agent Skills to generate clinical trial metadata from mock shells.

### Architecture

**Agent Skills + MCP Tools:**

PRISM uses a two-layer architecture:
- **MCP Tools** - Provide low-level operations (extract, validate, save)
- **Agent Skills** - Orchestrate workflows (how to use tools together)

**Available Skills:**
- `prism-meta-generation` - Generate metadata from mock shells

**Available MCP Tools:**
- `extract_mock_shell` - Extract mock shell data
- `validate_meta_definitions` - Validate metadata format
- `save_meta_definitions` - Save metadata to Excel
- `update_meta_definitions` - Update existing metadata
- `get_als_fields` - Query ALS fields (for derivations)
- `list_deliverables` - List deliverables from mock shell
- `load_meta_to_db` - Load metadata to database

### Usage

In OpenCode, simply say:
```
Generate metadata for this mock shell: path/to/shell.docx
```

OpenCode will:
1. Load the `prism-meta-generation` skill
2. Call MCP tools as needed
3. Generate metadata using Claude Opus 4.6
4. Validate and save results

### MCP Tools

All operations are done through MCP tools in OpenCode:

#### Meta Tools
- `load_meta(meta_path, db_path?)` - Load metadata to database
- `extract_mock_shell(mock_path, output_path?)` - Extract mock shell to JSON
- `list_mock_deliverables(mock_path)` - List deliverables from mock shell
- `list_db_deliverables(db_path, type?)` - List deliverables from database
- `get_variable_details(db_path, var_name)` - Get variable transformation details

#### Silver Tools
- `generate_silver(schema, db_path, als_path?, output_dir?)` - Generate Silver transforms
- `list_silver_transforms()` - List registered Silver transforms
- `get_transform_code(transform_name)` - Get transform source code
- `get_meta_variables(db_path, schema)` - Get variables from meta tables

#### Gold Tools
- `generate_gold(schema, db_path, output_dir?)` - Generate Gold statistics
- `list_gold_transforms()` - List registered Gold transforms

#### Platinum Tools
- `generate_platinum(db_path, ids?, type?, output?)` - Generate PPTX slide deck
- `preview_platinum_deliverable(db_path, deliverable_id)` - Preview deliverable slides

#### Utility Tools
- `lookup_als_field(als_path, domain?, keywords?)` - Look up ALS fields
- `get_bronze_schema(db_path)` - Get Bronze layer schema

**Total:** 15 MCP tools available

### Module Structure

| Directory/File | Purpose |
|----------------|---------|
| `.opencode/skills/` | OpenCode Agent Skills |
| `prism-meta-generation/` | Generate metadata from mock shells |
| `definitions/` | Meta definition models |
| `derivations/` | Derivation rules (future) |
| `extractor.py` | Parse mock shell to structured JSON |
| `loader.py` | Load metadata to meta tables |
| `excel_writer.py` | Formatted Excel output |
| `als_parser.py` | ALS parsing |
| `mcp/server.py` | MCP server with tools |

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
