-- ============================================================================
-- PRISM-DB Metadata Schema Initialization
-- Version: 3.0
-- Date: 2026-02-12
-- Description: Creates all metadata tables for PRISM-DB
-- ============================================================================

-- Create metadata schema
CREATE SCHEMA IF NOT EXISTS meta;

-- ============================================================================
-- meta.schema_docs - Database Schema Documentation
-- ============================================================================
CREATE TABLE IF NOT EXISTS meta.schema_docs (
    layer TEXT NOT NULL,                -- 'bronze', 'silver', 'gold'
    table_name TEXT NOT NULL,
    column_name TEXT NOT NULL,
    data_type TEXT NOT NULL,
    description TEXT,
    source TEXT,                        -- Source of the column (ALS field, derivation_id, etc.)
    example_values TEXT,                -- JSON array of example values
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (layer, table_name, column_name)
);

COMMENT ON TABLE meta.schema_docs IS 'Documentation of database schema for all layers';

-- ============================================================================
-- meta.data_catalog - Variable Registry
-- ============================================================================
CREATE TABLE IF NOT EXISTS meta.data_catalog (
    var_name TEXT NOT NULL,
    schema TEXT NOT NULL,               -- 'baseline', 'longitudinal', 'occurrence'
    layer TEXT NOT NULL,                -- 'bronze', 'silver'
    label TEXT,
    data_type TEXT,
    source_form TEXT,                   -- Source form OID from ALS
    source_field TEXT,                  -- Source field OID from ALS
    codelist TEXT,                      -- JSON: {"1": "Male", "2": "Female"}
    is_derived BOOLEAN DEFAULT FALSE,
    derivation_id TEXT,
    study_code TEXT DEFAULT '',         -- Empty string for cross-study variables
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (var_name, schema, layer, study_code)
);

COMMENT ON TABLE meta.data_catalog IS 'Registry of all variables across Bronze and Silver layers';

-- ============================================================================
-- meta.derivations - Transformation Rules
-- ============================================================================
CREATE TABLE IF NOT EXISTS meta.derivations (
    derivation_id TEXT PRIMARY KEY,
    target_var TEXT NOT NULL,
    target_schema TEXT NOT NULL,        -- 'baseline', 'longitudinal', 'occurrence'
    
    depends_on TEXT,                    -- JSON array: ["var1", "var2"]
    transformation_sql TEXT NOT NULL,   -- SQL for transformation
    complexity TEXT CHECK (complexity IN ('simple', 'medium', 'complex')),
    
    description TEXT,
    rule_doc TEXT,                      -- Path to external markdown documentation
    
    study_overrides TEXT,               -- JSON: {"STUDY001": "override SQL"}
    
    execution_order INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT
);

COMMENT ON TABLE meta.derivations IS 'Transformation rules for generating Silver layer from Bronze';

CREATE INDEX idx_derivations_target ON meta.derivations(target_schema, target_var);
CREATE INDEX idx_derivations_order ON meta.derivations(execution_order);

-- ============================================================================
-- meta.output_spec - Output Definitions
-- ============================================================================
CREATE TABLE IF NOT EXISTS meta.output_spec (
    output_id TEXT PRIMARY KEY,
    output_type TEXT CHECK (output_type IN ('table', 'listing', 'figure')),
    schema TEXT CHECK (schema IN ('baseline', 'longitudinal', 'occurrence')),
    
    -- Data requirements
    source_table TEXT,                  -- 'silver.baseline', etc.
    required_vars TEXT,                 -- JSON array: ["AGE", "SEX", "TRTA"]
    required_params TEXT,               -- JSON array for longitudinal: ["ALT", "AST"]
    filter_condition TEXT,              -- SQL WHERE clause
    
    -- Grouping configuration
    group_by TEXT,                      -- JSON: {"group1": "TRTA", "group2": "SEX"}
    comparison TEXT,                    -- 'pairwise', 'vs_control', NULL
    
    -- Statistical requirements
    stats_required TEXT,                -- JSON: ["n", "mean", "sd", "p_value"]
    analysis_method TEXT,               -- 'descriptive', 'ttest', 'anova', 'mmrm', 'coxph'
    analysis_spec TEXT,                 -- JSON: additional parameters for complex analyses
    
    -- Display configuration
    title_template TEXT,
    footnote_template TEXT,
    
    -- Study-specific overrides
    study_overrides TEXT,               -- JSON: study-specific configurations
    
    -- Organization
    block TEXT,                         -- Grouping for organization
    sort_order INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT
);

COMMENT ON TABLE meta.output_spec IS 'Definitions of outputs and their statistical requirements';

CREATE INDEX idx_output_spec_schema ON meta.output_spec(schema);
CREATE INDEX idx_output_spec_block ON meta.output_spec(block);

-- ============================================================================
-- meta.output_assembly - Assembly Instructions
-- ============================================================================
CREATE TABLE IF NOT EXISTS meta.output_assembly (
    output_id TEXT NOT NULL,
    component_type TEXT CHECK (component_type IN ('row', 'column', 'layer', 'panel')),
    component_order INTEGER NOT NULL,
    
    select_condition TEXT,              -- SQL WHERE clause to filter Gold data
    layout_template TEXT,               -- 'by_variable', 'by_visit', 'by_category'
    formatting_rules TEXT,              -- JSON: formatting specifications
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (output_id, component_order),
    FOREIGN KEY (output_id) REFERENCES meta.output_spec(output_id)
);

COMMENT ON TABLE meta.output_assembly IS 'Instructions for assembling Gold data into final outputs';

CREATE INDEX idx_output_assembly_output ON meta.output_assembly(output_id);

-- ============================================================================
-- Audit and Version Control
-- ============================================================================

CREATE TABLE IF NOT EXISTS meta.audit_log (
    log_id INTEGER PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    layer TEXT,
    operation TEXT,                     -- 'CREATE', 'UPDATE', 'DELETE', 'EXECUTE'
    table_name TEXT,
    record_id TEXT,
    user_name TEXT,
    description TEXT,
    sql_executed TEXT
);

COMMENT ON TABLE meta.audit_log IS 'Audit trail of all metadata changes and ETL executions';

CREATE INDEX idx_audit_log_timestamp ON meta.audit_log(timestamp);
CREATE INDEX idx_audit_log_layer ON meta.audit_log(layer);

-- ============================================================================
-- Helper Views
-- ============================================================================

-- View: All variables with their derivation status
CREATE OR REPLACE VIEW meta.v_variable_registry AS
SELECT 
    var_name,
    schema,
    layer,
    label,
    is_derived,
    d.derivation_id,
    d.complexity,
    d.is_active as derivation_active
FROM meta.data_catalog c
LEFT JOIN meta.derivations d ON c.derivation_id = d.derivation_id;

-- View: Output summary
CREATE OR REPLACE VIEW meta.v_output_summary AS
SELECT 
    s.output_id,
    s.output_type,
    s.schema,
    s.analysis_method,
    s.block,
    COUNT(a.component_order) as num_components,
    s.is_active
FROM meta.output_spec s
LEFT JOIN meta.output_assembly a ON s.output_id = a.output_id
GROUP BY s.output_id, s.output_type, s.schema, s.analysis_method, s.block, s.is_active;

-- ============================================================================
-- Insert Default Configuration
-- ============================================================================

-- Insert schema version
INSERT INTO meta.schema_docs (layer, table_name, column_name, data_type, description)
VALUES ('meta', 'schema_version', 'version', 'TEXT', 'PRISM-DB Schema Version 3.0');

-- ============================================================================
-- Metadata Initialization Complete
-- ============================================================================

SELECT 'PRISM-DB metadata schema initialized successfully' AS status;
