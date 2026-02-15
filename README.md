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
│   ├── sql/            # DDL scripts
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
| Meta | `meta.*` | 11 metadata tables (variables, derivations, outputs, etc.) |
| Bronze | `bronze.*` | Raw EDC data (one table per form) |
| Silver | `silver.baseline/longitudinal/occurrence` | Subject-level derived data |
| Gold | `gold.baseline/longitudinal/occurrence` | Group-level statistics |

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

## License

MIT
