---
name: prism-meta-generation
description: Use when generating metadata definitions from mock shell documents for clinical trial data
---

# PRISM Meta Generation

## Overview

Generate MetaDefinitions from mock shell documents using MCP tools and Claude Opus 4.6.

**Core principle:** One-shot generation with confidence levels, then iterate on low-confidence items.

## When to Use

- User provides mock shell file (docx/xlsx)
- Need to generate Silver variable definitions
- Need to create parameter definitions
- Need Gold statistics definitions
- Need Platinum deliverable definitions

## Process

### Phase 1: Generate

1. Ask for mock shell path
2. Call `extract_mock_shell` MCP tool
3. Use Claude Opus 4.6 to generate metadata:
   - Process all deliverables at once (no batching)
   - Set confidence for each variable (high/medium/low)
   - Mark uncertain as low confidence
4. Call `validate_meta_definitions` MCP tool
5. Ask for output path
6. Call `save_meta_definitions` MCP tool
7. Report statistics

### Phase 2: Review

1. Show low confidence items
2. Discuss with user
3. Call `update_meta_definitions` MCP tool
4. Re-validate and save

## Required MCP Tools

**REQUIRED:** These tools must be available:
- `extract_mock_shell` - Extract mock shell data
- `validate_meta_definitions` - Validate format
- `save_meta_definitions` - Save to Excel
- `update_meta_definitions` - Update existing metadata

## Tips

- Use 200K context models (Claude Opus 4.6, GLM-5)
- Process all deliverables at once
- Pay attention to footnotes and programming notes
- Mark unclear definitions as low confidence
- Review low confidence items with user

## Output Format

MetaDefinitions includes:
- `silver_variables` - Variable definitions with description
- `params` - Parameter definitions
- `gold_statistics` - Statistics definitions
- `platinum_deliverables` - Deliverable definitions
- `confidence_notes` - Items needing review

## Example

**User:** "Generate metadata for this mock shell: shell.docx"

**You should:**
1. Call `extract_mock_shell("shell.docx")`
2. Process data with Claude Opus 4.6
3. Validate with `validate_meta_definitions`
4. Save with `save_meta_definitions`
5. Report results

**User:** "Update the xxx_flg variable"

**You should:**
1. Discuss the update
2. Call `update_meta_definitions`
3. Re-validate and save
