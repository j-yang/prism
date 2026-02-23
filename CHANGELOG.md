# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- New Gold layer data dictionary (`meta.gold_dictionary`) for group-level statistics
- New Platinum layer deliverable definition (`meta.platinum_dictionary`) for table/figure/listing
- `selection` field in gold_dictionary for filter conditions (visit, domain, saefl, etc.)
- `statistics` JSON field in gold_dictionary for flexible statistic types
- `elements` JSON field in platinum_dictionary for referenced elements
- `deliverable_id` field in gold_dictionary to link with platinum deliverables

### Changed
- **BREAKING**: Renamed `meta.bronze_variables` → `meta.bronze_dictionary`
- **BREAKING**: Renamed `meta.silver_variables` → `meta.silver_dictionary`
- **BREAKING**: Removed `meta.outputs` table (replaced by `meta.platinum_dictionary`)
- **BREAKING**: Removed `meta.output_variables` table
- **BREAKING**: Removed `meta.output_params` table
- **BREAKING**: Renamed `gold_dictionary.var_id` → `element_id` (统计对象：variable/param/coding)
- **BREAKING**: Gold tables now use JSON for statistics (one row per group+element+selection)
- Updated `MetadataManager` API to use new dictionary table names
- Updated Pydantic models to match new schema
- Renamed `OutputType` enum → `DeliverableType`
- Meta Schema version: 5.0 → 5.1
- Gold Schema version: 3.1 → 4.0

### Removed
- `meta.derivations` table (derivations now stored in `meta.silver_dictionary`)
- `meta.flags` table (replaced by `meta.attrs`)
- `meta.variables` unified table (replaced by separate bronze/silver/gold dictionaries)
- `meta.functions` table
- `platinum_dictionary.render_function` field
- `platinum_dictionary.render_options` field
- `Output`, `OutputVariable`, `OutputParam`, `Variable`, `Derivation`, `Function` Pydantic models
- `add_variable`, `get_variables`, `get_variable` methods in MetadataManager
- `add_derivation`, `get_derivations`, `get_derivation_for_var` methods in MetadataManager
- `add_output`, `get_outputs`, `get_output` methods in MetadataManager
- `add_output_variable`, `get_output_variables` methods in MetadataManager
- `add_output_param`, `get_output_params` methods in MetadataManager
- `add_function`, `get_functions`, `get_function` methods in MetadataManager
- `add_flag`, `get_flags` methods in MetadataManager
- `get_missing_derivations`, `get_execution_order`, `get_output_full_spec` methods in MetadataManager

## [0.1.0] - 2024-XX-XX

### Added
- Initial PRISM architecture with Medallion layers (Bronze, Silver, Gold, Platinum)
- ALS parser for metadata extraction
- Silver SQL generator with template and LLM support
- Gold Python script generator
- Metadata manager with 11 tables
- DuckDB database integration

---

## Schema Versions

| Version | Date | Changes |
|---------|------|---------|
| v5.1 | 2026-02-17 | gold_dictionary: var_id→element_id, 复合PK; gold表用JSON存statistics; platinum移除render字段 |
| v5.0 | 2026-02-16 | Meta schema redesign: *_dictionary tables, gold_dictionary, platinum_dictionary |
| v4.0 | 2026-02-16 | Previous meta schema with outputs, output_variables, output_params |
