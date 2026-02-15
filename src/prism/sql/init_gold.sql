-- ============================================================================
-- PRISM-DB Gold Schema Initialization
-- Version: 3.1
-- Date: 2026-02-14
-- Description: Creates all 3 Gold tables for aggregated statistics
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS gold;

-- ============================================================================
-- 1. gold.baseline - Group-level baseline statistics
-- ============================================================================
CREATE TABLE IF NOT EXISTS gold.baseline (
    output_id TEXT NOT NULL,
    
    group1_name TEXT,
    group1_value TEXT,
    group2_name TEXT,
    group2_value TEXT,
    
    comparison TEXT,
    
    variable TEXT NOT NULL,
    category TEXT,
    
    stat_name TEXT NOT NULL,
    stat_value REAL,
    stat_display TEXT,
    row_order INTEGER,
    
    created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE gold.baseline IS '组别汇总统计 - baseline schema';

CREATE INDEX IF NOT EXISTS idx_gold_baseline_output ON gold.baseline(output_id);
CREATE INDEX IF NOT EXISTS idx_gold_baseline_group ON gold.baseline(group1_name, group1_value);
CREATE INDEX IF NOT EXISTS idx_gold_baseline_variable ON gold.baseline(variable);

-- ============================================================================
-- 2. gold.longitudinal - Group-level longitudinal statistics
-- ============================================================================
CREATE TABLE IF NOT EXISTS gold.longitudinal (
    output_id TEXT NOT NULL,
    
    group1_name TEXT,
    group1_value TEXT,
    group2_name TEXT,
    group2_value TEXT,
    
    comparison TEXT,
    
    paramcd TEXT,
    visit TEXT,
    visitnum INTEGER,
    
    stat_name TEXT NOT NULL,
    stat_value REAL,
    stat_display TEXT,
    row_order INTEGER,
    
    created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE gold.longitudinal IS '组别汇总统计 - longitudinal schema';

CREATE INDEX IF NOT EXISTS idx_gold_long_output ON gold.longitudinal(output_id);
CREATE INDEX IF NOT EXISTS idx_gold_long_group ON gold.longitudinal(group1_name, group1_value);
CREATE INDEX IF NOT EXISTS idx_gold_long_paramcd ON gold.longitudinal(paramcd);

-- ============================================================================
-- 3. gold.occurrence - Group-level occurrence statistics
-- ============================================================================
CREATE TABLE IF NOT EXISTS gold.occurrence (
    output_id TEXT NOT NULL,
    
    group1_name TEXT,
    group1_value TEXT,
    group2_name TEXT,
    group2_value TEXT,
    
    comparison TEXT,
    
    cat1_name TEXT,
    cat1_value TEXT,
    cat2_name TEXT,
    cat2_value TEXT,
    
    stat_name TEXT NOT NULL,
    stat_value REAL,
    stat_display TEXT,
    row_order INTEGER,
    
    created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE gold.occurrence IS '组别汇总统计 - occurrence schema';

CREATE INDEX IF NOT EXISTS idx_gold_occ_output ON gold.occurrence(output_id);
CREATE INDEX IF NOT EXISTS idx_gold_occ_group ON gold.occurrence(group1_name, group1_value);

-- ============================================================================
-- Helper View: Output statistics summary
-- ============================================================================
CREATE OR REPLACE VIEW gold.v_output_stats AS
SELECT 
    'baseline' AS schema,
    output_id,
    COUNT(DISTINCT group1_value) AS n_groups,
    COUNT(DISTINCT variable) AS n_variables,
    COUNT(*) AS n_stats
FROM gold.baseline
GROUP BY output_id

UNION ALL

SELECT 
    'longitudinal' AS schema,
    output_id,
    COUNT(DISTINCT group1_value) AS n_groups,
    COUNT(DISTINCT paramcd) AS n_variables,
    COUNT(*) AS n_stats
FROM gold.longitudinal
GROUP BY output_id

UNION ALL

SELECT 
    'occurrence' AS schema,
    output_id,
    COUNT(DISTINCT group1_value) AS n_groups,
    COUNT(DISTINCT cat1_value) AS n_variables,
    COUNT(*) AS n_stats
FROM gold.occurrence
GROUP BY output_id;

SELECT 'PRISM-DB Gold Schema v3.1 initialized. 3 tables created.' AS status;
