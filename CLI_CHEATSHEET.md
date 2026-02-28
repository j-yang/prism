# PRISM CLI Cheatsheet

## Commands Overview

```bash
prism meta generate    # Generate metadata from mock shell
prism meta load        # Load metadata to database
prism silver generate  # Generate Silver transformations
prism gold generate    # Generate Gold statistics
prism platinum generate # Generate PowerPoint slide deck
```

---

## Meta Commands

### Generate Metadata

```bash
# Generate from mock shell
uv run prism meta generate --mock shell.docx --als als.xlsx -o meta.xlsx

# List deliverables only
uv run prism meta generate --mock shell.docx --als als.xlsx --list-only

# Generate for specific deliverables
uv run prism meta generate --mock shell.docx --als als.xlsx -d "14.1.1,14.2.1" -o meta.xlsx

# Debug single deliverable
uv run prism meta generate --mock shell.docx --als als.xlsx --debug 14.1.1 -v

# JSON output
uv run prism meta generate --mock shell.docx --als als.xlsx --format json -o meta.json
```

### Load Metadata

```bash
# Load to database
uv run prism meta load --meta meta.xlsx --db study.duckdb
```

### Extract Mock Shell

```bash
# Extract to JSON for inspection
uv run prism meta extract --mock shell.docx -o shell.json
```

---

## Silver Commands

### Generate Transformations

```bash
# Generate for baseline schema
uv run prism silver generate --schema baseline --db study.duckdb

# Generate for longitudinal schema
uv run prism silver generate --schema longitudinal --db study.duckdb

# Generate for occurrence schema
uv run prism silver generate --schema occurrence --db study.duckdb

# Specify output directory
uv run prism silver generate --schema baseline --db study.duckdb -o transforms/silver/

# With ALS context
uv run prism silver generate --schema baseline --db study.duckdb --als als.xlsx
```

### List Transforms

```bash
uv run prism silver list
```

---

## Gold Commands

### Generate Statistics

```bash
# Generate for baseline schema
uv run prism gold generate --schema baseline --db study.duckdb

# Generate for longitudinal schema
uv run prism gold generate --schema longitudinal --db study.duckdb

# Generate for occurrence schema
uv run prism gold generate --schema occurrence --db study.duckdb

# Specify output directory
uv run prism gold generate --schema baseline --db study.duckdb -o transforms/gold/
```

### List Transforms

```bash
uv run prism gold list
```

---

## Platinum Commands

### Generate Slide Deck

```bash
# Generate from all deliverables
uv run prism platinum generate --db study.duckdb -o report.pptx

# Generate for specific deliverables
uv run prism platinum generate --db study.duckdb -d "14.1.1,14.2.1" -o report.pptx

# Filter by type (table, figure, listing)
uv run prism platinum generate --db study.duckdb --type table
uv run prism platinum generate --db study.duckdb --type figure
uv run prism platinum generate --db study.duckdb --type listing
```

### List Deliverables

```bash
uv run prism platinum list --db study.duckdb
```

### Preview Slide Content

```bash
uv run prism platinum preview --db study.duckdb --deliverable-id 14.1.1
```

---

## LLM Providers

```bash
# Use DeepSeek (default)
uv run prism --provider deepseek meta generate ...

# Use Zhipu
uv run prism --provider zhipu meta generate ...
```

---

## Output Structure

### Meta Excel (meta.xlsx)

| Sheet | Description |
|-------|-------------|
| `study_config` | Population & visit definitions |
| `params` | Longitudinal parameters |
| `silver_variables` | Variable definitions |
| `platinum` | Deliverable metadata |
| `gold_statistics` | Statistics specs |
| `review_needed` | Items needing human review |

### Silver Output (generated/silver/*.py)

```python
# Auto-generated Polars transformation
import polars as pl
from prism.transforms.registry import register_transform

@register_transform("age_years")
def derive_age_years(df: pl.DataFrame) -> pl.DataFrame:
    """Age in years."""
    return df.with_columns([
        pl.col("age").alias("age_years")
    ])
```

### Gold Output (generated/gold/*.py)

```python
# Auto-generated statistical aggregation
import polars as pl
from prism.transforms.registry import register_transform

@register_transform("age_gold")
def compute_age_stats(df: pl.DataFrame) -> pl.DataFrame:
    """Age statistics by treatment group."""
    return df.group_by(["treatment_group"]).agg([
        pl.len().alias("n"),
        pl.col("age").mean().alias("mean"),
        pl.col("age").std().alias("sd"),
    ])
```

### Platinum Output (report.pptx)

- Title slide with study info
- Table slides with formatted data
- Figure slides with native PPTX charts
- Listing slides with data rows

---

## Common Workflows

### Full Pipeline

```bash
# 1. Generate metadata
uv run prism meta generate --mock shell.docx --als als.xlsx -o meta.xlsx

# 2. Load to database
uv run prism meta load --meta meta.xlsx --db study.duckdb

# 3. Generate Silver transformations
uv run prism silver generate --schema baseline --db study.duckdb

# 4. Generate Gold statistics
uv run prism gold generate --schema baseline --db study.duckdb

# 5. Generate slide deck
uv run prism platinum generate --db study.duckdb -o report.pptx
```

### Debug Workflow

```bash
# Debug metadata generation
uv run prism meta generate --mock shell.docx --als als.xlsx --debug 14.1.1 -v

# Preview slide content
uv run prism platinum preview --db study.duckdb --deliverable-id 14.1.1
```

---

## Environment Variables

```bash
# LLM API keys
export DEEPSEEK_API_KEY=sk-xxx
export ZHIPU_API_KEY=xxx
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No DEEPSEEK_API_KEY" | Set environment variable or create `.env` file |
| Empty silver variables | Check ALS file format, use --debug mode |
| Import errors | Run `uv sync` to install dependencies |
| LLM timeout | Use smaller batch or check network |
| Zhipu balance error | Top up account or use DeepSeek |
