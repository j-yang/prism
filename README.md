# PRISM

Clinical Trial Data Pipeline with AI-powered Code Generation.

## Overview

PRISM implements a Medallion architecture for clinical trial data:

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌───────────┐
│  Meta   │───▶│  Bronze │───▶│  Silver │───▶│   Gold    │
│ (Spec)  │    │  (Raw)  │    │(Derived)│    │ (Stats)   │
└─────────┘    └─────────┘    └─────────┘    └───────────┘
                                                       │
                                                       ▼
                                                ┌───────────┐
                                                │ Platinum  │
                                                │ (Reports) │
                                                └───────────┘
```

## Installation

```bash
pip install -e .
```

## Quick Start

```python
from prism import Database, MetadataManager, SilverGenerator, GoldEngine
from prism.meta import parse_als_to_db

# Initialize database
db = Database("study.duckdb")

# Parse ALS (creates bronze tables and meta.bronze_dictionary)
parse_als_to_db("path/to/als.xlsx", db, study_code="STUDY001")

# Manage metadata
meta = MetadataManager(db)

# Generate Silver layer SQL
silver = SilverGenerator(db)
silver.generate_all("generated/silver/")

# Generate Gold layer analysis
gold = GoldEngine(db)
gold.generate_all("generated/gold/")
```

## Project Structure

```
prism/
├── src/prism/
│   ├── core/           # Database, schema models
│   ├── sql/            # DDL scripts
│   ├── agent/          # LLM integration, templates
│   ├── meta/           # Metadata management, ALS parser
│   ├── spec/           # Spec Agent (mock shell → spec)
│   ├── bronze/         # Raw data import (SAS/CSV)
│   ├── silver/         # Data transformation
│   ├── gold/           # Statistical analysis
│   └── platinum/       # Report rendering
├── tests/
├── examples/
└── archive/            # Deprecated WASM portal
```

## Data Layers

| Layer | Schema | Description |
|-------|--------|-------------|
| Meta | `meta.*` | 10 metadata tables |
| Bronze | `bronze.*` | Raw EDC data (one table per form) |
| Silver | `silver.baseline/longitudinal/occurrence` | Subject-level derived data |
| Gold | `gold.baseline/longitudinal/occurrence` | Group-level statistics |
| Platinum | - | Report output (RTF/PDF/HTML) |

## Bronze Layer

**按原始 Form 存储，保持完整 Traceability**

- `bronze.ae` - Adverse Events
- `bronze.cm` - Concomitant Medications
- `bronze.dm` - Demographics
- `bronze.lb` - Laboratory
- `bronze.vs` - Vital Signs
- ... (N tables, one per form)

Processing rules:
- Column names: lowercase
- Date conversion: SAS date → DATE type
- No filtering by default

## Meta Schema (10 Tables)

### Configuration
| Table | Purpose |
|-------|---------|
| `meta.study_info` | Study 基本信息 |
| `meta.visits` | 分析 Visit 定义 |
| `meta.form_classification` | Form → Domain/Schema 映射 |

### Dictionaries
| Table | Purpose |
|-------|---------|
| `meta.bronze_dictionary` | Bronze 层数据字典（来自 ALS） |
| `meta.silver_dictionary` | Silver 层数据字典（来自 Spec） |
| `meta.gold_dictionary` | Gold 层数据字典（来自 Spec） |
| `meta.platinum_dictionary` | Platinum 交付物定义 |

### Definitions
| Table | Purpose |
|-------|---------|
| `meta.params` | Longitudinal 参数定义 |
| `meta.attrs` | Occurrence 扩展字段定义 |
| `meta.dependencies` | 变量依赖关系 |

## Agent

PRISM uses DeepSeek LLM to generate SQL and Python code:

- **Simple derivations**: Hardcoded Jinja2 templates
- **Complex derivations**: LLM-generated code (needs review)

Set your API key:
```bash
export DEEPSEEK_API_KEY=your_key_here
```

## Spec Agent

Automated spec generation from mock shell documents:

```bash
# Generate spec from mock shell
prism spec generate --mock shell.docx --als als.xlsx --output spec.xlsx

# List deliverables only
prism spec generate --mock shell.docx --als als.xlsx --list-only

# Learn from corrections
prism spec learn --original draft.json --corrected final.json --study STUDY001

# View learned patterns
prism spec patterns stats
```

Output Excel contains 6 sheets:
- `study_config` - Populations, event periods
- `params` - Longitudinal parameter definitions
- `silver_variables` - Variables with derivation SQL
- `platinum` - Deliverable definitions
- `gold_statistics` - Statistics definitions
- `review_needed` - Items requiring human review

Memory store at `~/.prism/memory.duckdb` enables cross-study learning.

## Testing

```bash
PYTHONPATH=src pytest tests/
```

## Documentation

- **ARCHITECTURE.md** - Detailed architecture and schema design
- **ALS_PLAN.md** - ALS parser design notes

## License

MIT
