# PRISM MCP Server

PRISM provides an MCP (Model Context Protocol) server that allows you to use PRISM capabilities directly from OpenCode, Claude Desktop, or other MCP-compatible AI tools.

## What is MCP?

MCP is an open protocol that enables AI applications to securely connect to data sources and tools. Think of it like a USB-C port for AI applications - a standardized way to connect PRISM to any MCP-compatible agent.

## Available Tools

PRISM MCP Server exposes the following tools:

| Tool | Description |
|------|-------------|
| `generate_meta` | Generate metadata from mock shell and ALS |
| `load_meta` | Load metadata into DuckDB meta tables |
| `generate_silver` | Generate Silver layer Polars code |
| `generate_gold` | Generate Gold layer statistics code |
| `lookup_als_field` | Look up ALS fields by domain/keywords |
| `get_bronze_schema` | Get Bronze layer table schema |
| `get_meta_variables` | Get variables from meta.silver_dictionary |
| `list_deliverables` | List all deliverables from mock shell |

## Installation

PRISM MCP Server is installed as part of the PRISM package:

```bash
uv sync
```

## Configuration

### OpenCode

Add PRISM to your OpenCode configuration:

```json
// ~/.config/opencode/config.json
{
  "mcpServers": {
    "olympus": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/YOUR_USERNAME/projects/olympus",
        "run",
        "olympus-mcp"
      ]
    }
  }
}
```

### Claude Desktop

Add PRISM to your Claude Desktop configuration:

```json
// ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "olympus": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/YOUR_USERNAME/projects/olympus",
        "run",
        "olympus-mcp"
      ]
    }
  }
}
```

## Usage Examples

Once configured, you can interact with PRISM through natural language:

### Example 1: Generate Metadata

```
User: Generate metadata for the some_study project

Agent: I'll help you generate metadata. Let me first check what files are available...

[Uses list_deliverables tool]

Found 34 deliverables. Now generating metadata...

[Uses generate_meta tool]

Generated metadata:
  Silver variables: 45
  Params: 12
  Items needing review: 3
  Output: examples/some_study/generated_meta.xlsx

Would you like me to load this into the database?
```

### Example 2: Generate Silver Code

```
User: Generate Silver layer code for baseline schema

Agent: [Uses generate_silver tool]

Generated 28 transforms for baseline:
  High confidence: 20
  Medium confidence: 6
  Low confidence (needs review): 2
  Output: generated/silver/baseline.py

Review transforms marked with WARNING comments.
```

### Example 3: Query ALS Fields

```
User: What ALS fields are related to adverse events?

Agent: [Uses lookup_als_field tool]

Found 156 matching fields for domain AE:

  AE.AETERM
    Label: Adverse Event Term
    Domain: AE
    Type: TEXT

  AE.AESTDAT
    Label: Start Date
    Domain: AE
    Type: DATE

  ... and 154 more
```

## Mode Selection

PRISM supports three generation modes:

### Auto Mode (Default)
- Automatically generates all variables
- Low confidence items marked in Excel
- Review after generation
- Best for: Routine generation, large batches

### Interactive Mode
- Pauses for confirmation on low-confidence items
- Asks user to clarify ambiguities
- Best for: Complex studies, new domains

### Discussion Mode
- Discusses each variable with user
- Good for defining new rules
- Best for: Learning, research, difficult cases

Specify mode when calling tools:

```
User: Generate metadata in interactive mode

Agent: I'll use interactive mode and ask you about uncertain items...
```

## Benefits of MCP Integration

| Feature | CLI | MCP Agent |
|---------|-----|-----------|
| Natural language | ❌ | ✅ |
| Dynamic context | ❌ | ✅ |
| Ask clarifications | ❌ | ✅ |
| Multi-step workflows | ❌ | ✅ |
| No API key needed | ❌ | ✅ (uses agent's subscription) |

## Architecture

```
OpenCode / Claude Desktop / VS Code
         │
         │ MCP Protocol
         ↓
┌─────────────────────────────┐
│   PRISM MCP Server          │
│   (olympus-mcp command)       │
│                             │
│   Tools:                    │
│   - generate_meta           │
│   - generate_silver         │
│   - lookup_als_field        │
│   - ...                     │
└─────────────────────────────┘
         │
         │ Python calls
         ↓
┌─────────────────────────────┐
│   PRISM Core                │
│   - MetaAgent (PydanticAI)  │
│   - SilverAgent             │
│   - GoldAgent               │
│   - ToolRegistry            │
└─────────────────────────────┘
         │
         │ LLM API
         ↓
    DeepSeek / Zhipu
```

## Troubleshooting

### MCP Server not found

Make sure `olympus-mcp` is in your PATH:

```bash
uv run which olympus-mcp
```

### Import errors

Ensure all dependencies are installed:

```bash
uv sync
```

### Permission errors

Check file permissions for your project directory.

## Next Steps

1. Configure your MCP client (OpenCode/Claude)
2. Try the examples above
3. Review generated code
4. Provide feedback on accuracy

## Resources

- [MCP Documentation](https://modelcontextprotocol.io/)
- [PRISM Documentation](./README.md)
- [Architecture Guide](./ARCHITECTURE.md)
