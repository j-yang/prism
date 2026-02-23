# PRISM

Clinical Trial Data Pipeline with AI-powered Code Generation.

## Overview

PRISM implements a Medallion architecture for clinical trial data:

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌───────────┐
│  Meta   │───▶│  Bronze │───▶│  Silver │───▶│   Gold     │
│ (Spec)  │    │  (Raw)  │    │(Derived)│    │  (Stats)   │
└─────────┘    └─────────┘    └─────────┘    └───────────┘
                                                     │
                                                     ▼
                                              ┌───────────┐
                                              │  Platinum  │
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

# Initialize database
db = Database("study.duckdb")

# Manage metadata
meta = MetadataManager(db)
meta.set_study_info(study_code="STUDY001")

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
│   ├── sql/            # DDL scripts (init_meta.sql v5.0)
│   ├── agent/          # LLM integration, templates
│   ├── meta/           # Metadata management, ALS parser
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
| Meta | `meta.*` | 10 metadata tables (dictionaries, deliverables, dependencies) |
| Bronze | `bronze.*` | Raw EDC data (one table per form) |
| Silver | `silver.baseline/longitudinal/occurrence` | Subject-level derived data |
| Gold | `gold.baseline/longitudinal/occurrence` | Group-level statistics |

## Meta Schema (v5.0)

### Dictionaries
| Table | Purpose |
|-------|---------|
| `meta.bronze_dictionary` | Bronze层数据字典 |
| `meta.silver_dictionary` | Silver层数据字典 |
| `meta.gold_dictionary` | Gold层数据字典 (Group Level) |

### Deliverables
| Table | Purpose |
|-------|---------|
| `meta.platinum_dictionary` | Platinum交付物定义 (table/figure/listing) |

### Configuration
| Table | Purpose |
|-------|---------|
| `meta.study_info` | Study基本信息 |
| `meta.params` | Longitudinal参数定义 |
| `meta.attrs` | Occurrence domain扩展字段定义 |
| `meta.visits` | Analysis visit definitions |
| `meta.form_classification` | Form分类映射 |
| `meta.dependencies` | 变量依赖关系 |

## Agent

PRISM uses DeepSeek LLM to generate SQL and Python code:

- **Simple derivations**: Hardcoded Jinja2 templates
- **Complex derivations**: LLM-generated code (needs review)

Set your API key:
```bash
export DEEPSEEK_API_KEY=your_key_here
```

## Testing

```bash
PYTHONPATH=src pytest tests/
```

## Documentation

- **ARCHITECTURE.md** - Detailed architecture and schema design
- **CHANGELOG.md** - Version history and changes

## License

MIT
