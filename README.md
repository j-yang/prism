# PRISM

Clinical Trial Data Pipeline with AI-powered Code Generation.

## Overview

PRISM implements a Medallion architecture for clinical trial data with unified PydanticAI agents:

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌───────────┐
│  Meta   │───▶│  Bronze │───▶│  Silver │───▶│   Gold    │
│ (Spec)  │    │  (Raw)  │    │(Derived)│    │ (Stats)   │
└─────────┘    └─────────┘    └─────────┘    └───────────┘
     │              │              │              │
     └──────────────┴──────────────┴──────────────┘
                          │
                   ┌──────▼──────┐
                   │  Platinum   │
                   │ (Slide Deck)│
                   └─────────────┘
```

## Installation

```bash
# Clone and setup
git clone <repo-url>
cd prism
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env and add your API keys (DEEPSEEK_API_KEY, ZHIPU_API_KEY)
```

## Quick Start

### Option 1: CLI (Batch Mode)

```bash
# 1. Generate metadata from mock shell
uv run prism meta generate --mock shell.docx --als als.xlsx -o meta.xlsx

# 2. Load metadata to database
uv run prism meta load --meta meta.xlsx --db study.duckdb

# 3. Generate Silver transformations
uv run prism silver generate --schema baseline --db study.duckdb

# 4. Generate Gold statistics
uv run prism gold generate --schema baseline --db study.duckdb

# 5. Generate PowerPoint slide deck
uv run prism platinum generate --db study.duckdb -o report.pptx
```

### Option 2: MCP Server (Interactive Mode)

PRISM provides an MCP Server for use with OpenCode, Claude Desktop, and other MCP-compatible AI tools.

**Setup:**
```bash
# Configure OpenCode
cat > ~/.config/opencode/config.json << 'EOF'
{
  "mcpServers": {
    "prism": {
      "command": "uv",
      "args": ["--directory", "/path/to/prism", "run", "prism-mcp"]
    }
  }
}
EOF

# Restart OpenCode
opencode
```

**Usage:**
```
User: 帮我列出some_study的deliverables

OpenCode: [调用 list_deliverables tool]
         Found 34 deliverables:
         - 14.1.1 CAR-T Treatment Summary
         - 14.1.2.1 Baseline Characteristics (IIM Cohort)
         ...

User: 生成metadata

OpenCode: [调用 generate_meta tool]
         生成了45个变量
         输出：meta.xlsx
```

**Available MCP Tools:**
- `list_deliverables` - List deliverables from mock shell
- `lookup_als_field` - Query ALS fields by domain/keywords
- `get_bronze_schema` - Get Bronze layer table structure
- `get_meta_variables` - Get variables from meta tables
- `generate_meta` - Generate metadata (requires LLM)
- `load_meta` - Load metadata to DuckDB
- `generate_silver` - Generate Silver Polars code (requires LLM)
- `generate_gold` - Generate Gold statistics code (requires LLM)

See [MCP_GUIDE.md](MCP_GUIDE.md) for detailed usage.

## CLI Commands

### Meta (Metadata Generation)

```bash
# Generate metadata from mock shell
uv run prism meta generate --mock shell.docx --als als.xlsx -o meta.xlsx

# List deliverables
uv run prism meta generate --mock shell.docx --als als.xlsx --list-only

# Debug specific deliverable
uv run prism meta generate --mock shell.docx --als als.xlsx --debug 14.1.1 -v

# Load to database
uv run prism meta load --meta meta.xlsx --db study.duckdb
```

### Silver (Transformations)

```bash
# Generate Polars transformations for baseline schema
uv run prism silver generate --schema baseline --db study.duckdb

# Generate for longitudinal schema
uv run prism silver generate --schema longitudinal --db study.duckdb

# Generate for occurrence schema
uv run prism silver generate --schema occurrence --db study.duckdb
```

### Gold (Statistics)

```bash
# Generate statistical aggregations
uv run prism gold generate --schema baseline --db study.duckdb
uv run prism gold generate --schema longitudinal --db study.duckdb
uv run prism gold generate --schema occurrence --db study.duckdb
```

### Platinum (Slide Decks)

```bash
# Generate PowerPoint from all deliverables
uv run prism platinum generate --db study.duckdb -o report.pptx

# Generate for specific deliverables
uv run prism platinum generate --db study.duckdb -d "14.1.1,14.2.1"

# Filter by type
uv run prism platinum generate --db study.duckdb --type table

# List deliverables
uv run prism platinum list --db study.duckdb

# Preview slide content
uv run prism platinum preview --db study.duckdb --deliverable-id 14.1.1
```

## Project Structure

```
prism/
├── src/prism/
│   ├── core/           # Database, schema models, Pydantic models
│   ├── agent/          # LLM providers (zhipu, deepseek) + PydanticAI base
│   ├── meta/           # Metadata generation (agent, generator, loader)
│   ├── bronze/         # Raw data import (SAS/CSV/Excel)
│   ├── silver/         # Silver agent + transformation engine
│   ├── gold/           # Gold agent + statistics engine
│   ├── platinum/       # Platinum agent + PPTX renderer
│   └── transforms/     # Python transformations registry
├── tests/
├── examples/
└── archive/            # Deprecated code
```

## Data Layers

| Layer | Schema | Description |
|-------|--------|-------------|
| Meta | `meta.*` | 9 metadata tables |
| Bronze | `bronze.*` | Raw EDC data (one table per form) |
| Silver | `silver.baseline/longitudinal/occurrence` | Subject-level derived data |
| Gold | `gold.baseline/longitudinal/occurrence` | Group-level statistics |
| Platinum | - | PowerPoint slide decks |

## Meta Schema (9 Tables)

| Table | Purpose |
|-------|---------|
| `meta.study_info` | Study information |
| `meta.visits` | Analysis visit definitions |
| `meta.form_classification` | Form → Domain/Schema mapping |
| `meta.params` | Longitudinal parameter definitions |
| `meta.attrs` | Occurrence domain extended fields |
| `meta.bronze_dictionary` | Bronze layer data dictionary |
| `meta.silver_dictionary` | Silver layer data dictionary |
| `meta.gold_dictionary` | Gold layer statistics definitions |
| `meta.platinum_dictionary` | Platinum deliverable definitions |

## PydanticAI Architecture

All layers use unified PydanticAI agents:

```
┌─────────────────────────────────────────────────────────┐
│                    PydanticAI Agent                      │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │   Meta   │  │  Silver  │  │   Gold   │  │ Platinum │ │
│  │  Agent   │  │  Agent   │  │  Agent   │  │  Agent   │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘ │
│       │             │             │             │       │
│       └─────────────┴─────────────┴─────────────┘       │
│                          │                               │
│                   ┌──────▼──────┐                       │
│                   │ Shared Tools│                       │
│                   │ - ALS lookup│                       │
│                   │ - Meta vars │                       │
│                   │ - Deps check│                       │
│                   └─────────────┘                       │
└─────────────────────────────────────────────────────────┘
```

## LLM Providers

| Provider | Usage |
|----------|-------|
| DeepSeek (default) | `--provider deepseek` |
| Zhipu | `--provider zhipu` |

Set your API key:
```bash
export DEEPSEEK_API_KEY=your_key_here
# or
export ZHIPU_API_KEY=your_key_here
```

## Development

```bash
# Run tests
uv run pytest tests/ -v

# Format code
uv run --extra dev black src/prism/

# Lint code
uv run --extra dev ruff check src/prism/

# Type check
uv run --extra dev mypy src/prism/
```

## Documentation

- **AGENTS.md** - Coding agent guidelines
- **ARCHITECTURE.md** - Detailed architecture design
- **CLI_CHEATSHEET.md** - CLI command reference

## License

MIT
