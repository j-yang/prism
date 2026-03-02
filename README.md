# Olympus

Clinical Trial Data Pipeline with AI-powered Code Generation.

## Overview

Olympus implements a Medallion architecture for clinical trial data with unified PydanticAI agents:

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

Olympus provides an MCP Server for use with OpenCode, Claude Desktop, and other MCP-compatible AI tools.

**Setup:**
```bash
# Clone and setup
git clone <repo-url>
cd prism
uv sync

# Configure OpenCode
cat > ~/.config/opencode/config.json << 'EOF'
{
  "mcpServers": {
    "prism": {
      "command": "uv",
      "args": ["--directory", "/path/to/prism", "run", "olympus-mcp"]
    }
  }
}
EOF

# Restart OpenCode
opencode
```

**Usage Examples:**
```
User: 帮我列出some_study的deliverables

OpenCode: [调用 list_mock_deliverables tool]
         Found 34 deliverables:
         - 14.1.1 CAR-T Treatment Summary
         - 14.1.2.1 Baseline Characteristics (IIM Cohort)
         ...

User: 提取mock shell到JSON

OpenCode: [调用 extract_mock_shell tool]
         Extracted to mock_extracted.json
         Deliverables: 34

User: 加载metadata到数据库

OpenCode: [调用 load_meta tool]
         Loaded to study.duckdb:
           Silver variables: 45
           Params: 12

User: 生成Silver transforms

OpenCode: [调用 generate_silver tool]
         Generated 23 transforms for baseline:
           High confidence: 18
           Medium confidence: 5

User: 生成PPTX

OpenCode: [调用 generate_platinum tool]
         Generated slide deck:
           Slides: 67
           Deliverables: 34
```

**Available MCP Tools (15):**

| Category | Tools |
|----------|-------|
| **Meta** | `load_meta`, `extract_mock_shell`, `list_mock_deliverables`, `list_db_deliverables`, `get_variable_details` |
| **Silver** | `generate_silver`, `list_silver_transforms`, `get_transform_code`, `get_meta_variables` |
| **Gold** | `generate_gold`, `list_gold_transforms` |
| **Platinum** | `generate_platinum`, `preview_platinum_deliverable` |
| **Utility** | `lookup_als_field`, `get_bronze_schema` |

See [AGENTS.md](AGENTS.md) for detailed tool documentation.

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

- **AGENTS.md** - Coding agent guidelines and MCP tools reference
- **ARCHITECTURE.md** - Detailed architecture design

## License

MIT
