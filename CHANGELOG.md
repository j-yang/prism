# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.1.0] - 2025-03-01

### Added

#### MCP Server Integration
- **PRISM MCP Server** (`src/prism/mcp/server.py`)
  - Full MCP protocol support for OpenCode, Claude Desktop, etc.
  - 8 MCP tools exposed:
    - `list_deliverables` - List deliverables from mock shell
    - `lookup_als_field` - Query ALS fields by domain/keywords
    - `get_bronze_schema` - Get Bronze layer table structure
    - `get_meta_variables` - Get variables from meta tables
    - `generate_meta` - Generate metadata (requires LLM)
    - `load_meta` - Load metadata to DuckDB
    - `generate_silver` - Generate Silver Polars code (requires LLM)
    - `generate_gold` - Generate Gold statistics code (requires LLM)
  - Entry point: `prism-mcp` command

#### Documentation
- **MCP_GUIDE.md** - Comprehensive MCP usage guide
- **MCP_SETUP.md** - Configuration and setup instructions

### Changed

#### Architecture
- Removed old provider system (`agent/provider.py`, `agent/deepseek.py`, `agent/zhipu.py`)
- Unified all LLM calls under PydanticAI
- `MetaGenerator` now uses PydanticAI (was using old provider)
- `GoldEngine` deprecated (use `GoldAgent` instead)

#### Dependencies
- Added `mcp[cli]>=1.2.0` for MCP server support
- PydanticAI now the sole LLM interface

### Fixed
- **ALS field lookup** - Now correctly extracts domain from FormOID and uses DraftFieldName as label
- **Tool registry** - Improved ALS field loading with multiple fallback columns

## [1.0.0] - 2025-02-28

### Added

#### Unified PydanticAI Architecture
- **PydanticAI Base Agent** (`src/prism/agent/base.py`)
  - Shared infrastructure for all agents
  - Tool registry: ALS lookup, Bronze schema, Meta variables, Dependency check
  - Provider abstraction: DeepSeek, Zhipu
  - Structured output via Pydantic models

#### Meta Layer
- **MetaAgent** (`src/prism/meta/agent.py`) - PydanticAI agent for metadata generation
  - Batch processing (10 variables per call)
  - Structured output with Pydantic validation
- **Merged spec → meta** - All spec functionality moved to meta module
- **Meta CLI** - `prism meta generate`, `prism meta load`, `prism meta extract`

#### Silver Layer
- **SilverAgent** (`src/prism/silver/agent.py`) - PydanticAI agent for Silver transformations
  - Generates Polars Python code
  - Per-schema generation (baseline, longitudinal, occurrence)
  - Human reviews code before execution
- **Silver CLI** - `prism silver generate`, `prism silver list`

#### Gold Layer
- **GoldAgent** (`src/prism/gold/agent.py`) - PydanticAI agent for Gold statistics
  - Generates Polars statistical aggregations
  - Per-schema generation
  - Human reviews code before execution
- **Gold CLI** - `prism gold generate`, `prism gold list`

#### Platinum Layer
- **PlatinumAgent** (`src/prism/platinum/agent.py`) - PydanticAI agent for slide generation
- **PPTXRenderer** (`src/prism/platinum/renderer.py`) - PowerPoint rendering with python-pptx
  - Native PPTX charts (editable in PowerPoint)
  - Table slides, figure slides, listing slides
  - Combined output (all slides in one file)
- **Platinum CLI** - `prism platinum generate`, `prism platinum list`, `prism platinum preview`

### Changed

#### Architecture
- **BREAKING**: Unified all layers under PydanticAI
- **BREAKING**: Renamed `prism spec` → `prism meta`
- **BREAKING**: Moved `src/prism/spec/` → `src/prism/meta/`
- **BREAKING**: Silver/Gold now generate Python Polars code (not SQL)
- **BREAKING**: Platinum now generates PPTX slide decks (not RTF/PDF)

#### CLI
- Default provider changed from Zhipu to DeepSeek
- Added `--provider` flag to all commands
- All commands now use `uv run prism` pattern

#### Dependencies
- Added `pydantic-ai>=0.0.10`
- Added `python-pptx>=1.0.0`
- Added `httpx>=0.27.0`, `httpcore>=1.0.0`, `sniffio>=1.3.0`, `socksio>=1.0.0`

### Removed
- `src/prism/spec/` directory (merged into meta)
- `src/prism/sql/` directory (DDL now auto-generated from Pydantic)
- `src/prism/agent/templates/` directory (unused)
- Legacy pattern learning system (`matcher.py`, `learner.py`, `memory.py`)
- Test databases (`study.duckdb`, `test_prism_v31.duckdb`, `test_silver_gen.duckdb`)

### Documentation
- Rewrote `README.md` with new architecture
- Rewrote `ARCHITECTURE.md` with PydanticAI design
- Rewrote `CLI_CHEATSHEET.md` with new commands
- Removed outdated `ALS_PLAN.md`

---

## [0.1.0] - 2024-XX-XX

### Added
- Initial PRISM architecture with Medallion layers (Bronze, Silver, Gold, Platinum)
- ALS parser for metadata extraction
- Silver SQL generator with template and LLM support
- Gold Python script generator
- Metadata manager with 11 tables
- DuckDB database integration
- Spec Agent for mock shell parsing

---

## Schema Versions

| Version | Date | Changes |
|---------|------|---------|
| v6.0 | 2025-02-28 | Unified PydanticAI architecture, spec→meta merge |
| v5.1 | 2025-02-17 | gold_dictionary: var_id→element_id, JSON statistics |
| v5.0 | 2025-02-16 | Meta schema redesign: *_dictionary tables |
