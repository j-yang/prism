-- ============================================================================
-- PRISM-DB Traceability Schema
-- Version: 3.1
-- Date: 2026-02-14
-- Description: Creates tables for data lineage tracking (Gold → Silver → Bronze)
-- ============================================================================

-- ============================================================================
-- 1. meta.data_lineage - Gold → Silver 追溯
-- ============================================================================
CREATE TABLE IF NOT EXISTS meta.data_lineage (
    lineage_id TEXT PRIMARY KEY,
    
    -- 目标 (Gold 统计量)
    target_output_id TEXT NOT NULL,
    target_group_name TEXT,
    target_group_value TEXT,
    target_variable TEXT NOT NULL,
    target_category TEXT,
    target_stat_name TEXT NOT NULL,
    target_stat_value REAL,
    
    -- 来源 (Silver 数据)
    source_layer TEXT NOT NULL DEFAULT 'silver',
    source_table TEXT NOT NULL,
    source_subjects TEXT,              -- JSON array: ["001", "002", ...]
    source_record_count INTEGER,
    source_query TEXT,                 -- 原始查询 SQL
    
    -- 元信息
    analysis_script TEXT,              -- 生成脚本路径
    created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE meta.data_lineage IS '数据追溯: Gold统计量 → Silver数据';

CREATE INDEX IF NOT EXISTS idx_lineage_output ON meta.data_lineage(target_output_id);
CREATE INDEX IF NOT EXISTS idx_lineage_group ON meta.data_lineage(target_group_value);
CREATE INDEX IF NOT EXISTS idx_lineage_variable ON meta.data_lineage(target_variable);

-- ============================================================================
-- 2. meta.silver_sources - Silver → Bronze 追溯
-- ============================================================================
CREATE TABLE IF NOT EXISTS meta.silver_sources (
    id INTEGER PRIMARY KEY,
    
    -- Silver 层
    silver_table TEXT NOT NULL,        -- 'silver.baseline'
    silver_column TEXT NOT NULL,       -- 'age'
    
    -- Bronze 层来源
    bronze_table TEXT,                 -- 'bronze.dm'
    bronze_column TEXT,                -- 'AGE'
    
    -- 衍生信息
    derivation_id TEXT,                -- FK → meta.derivations
    derivation_type TEXT,              -- 'direct', 'derived', 'calculated'
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(silver_table, silver_column)
);

COMMENT ON TABLE meta.silver_sources IS '数据追溯: Silver变量 → Bronze来源';

CREATE INDEX IF NOT EXISTS idx_silver_sources_table ON meta.silver_sources(silver_table);
CREATE INDEX IF NOT EXISTS idx_silver_sources_derivation ON meta.silver_sources(derivation_id);

-- ============================================================================
-- Helper View: Full Lineage Chain
-- ============================================================================
CREATE OR REPLACE VIEW meta.v_full_lineage AS
SELECT 
    dl.target_output_id,
    dl.target_group_value,
    dl.target_variable,
    dl.target_stat_name,
    dl.source_table AS silver_table,
    ss.bronze_table,
    ss.bronze_column,
    ss.derivation_type,
    dl.source_subjects,
    dl.source_record_count
FROM meta.data_lineage dl
LEFT JOIN meta.silver_sources ss 
    ON ss.silver_table = REPLACE(dl.source_table, 'silver.', 'silver.')
ORDER BY dl.target_output_id, dl.target_variable;

SELECT 'PRISM-DB Traceability Schema initialized. 2 tables created.' AS status;
