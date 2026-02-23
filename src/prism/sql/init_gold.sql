-- ============================================================================
-- PRISM-DB Gold Schema Initialization
-- Version: 4.0
-- Date: 2026-02-17
-- Description: Creates all 3 Gold tables for aggregated statistics
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS gold;

-- ============================================================================
-- 1. gold.baseline - Group-level baseline statistics
-- ============================================================================
CREATE TABLE IF NOT EXISTS gold.baseline (
    deliverable_id TEXT NOT NULL,

    element_id TEXT NOT NULL,
    group_id TEXT NOT NULL,

    statistics JSON,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE gold.baseline IS '组别汇总统计 - baseline schema';
COMMENT ON COLUMN gold.baseline.element_id IS '变量名：age, sex, race等';
COMMENT ON COLUMN gold.baseline.group_id IS '分组值：Drug, Placebo等';
COMMENT ON COLUMN gold.baseline.statistics IS '{"n": 50, "mean": 45.2, "sd": 12.3} 或 {"n": 30, "pct": 60.0}';

CREATE INDEX IF NOT EXISTS idx_gold_baseline_deliverable ON gold.baseline(deliverable_id);
CREATE INDEX IF NOT EXISTS idx_gold_baseline_group ON gold.baseline(group_id);
CREATE INDEX IF NOT EXISTS idx_gold_baseline_element ON gold.baseline(element_id);

-- ============================================================================
-- 2. gold.longitudinal - Group-level longitudinal statistics
-- ============================================================================
CREATE TABLE IF NOT EXISTS gold.longitudinal (
    deliverable_id TEXT NOT NULL,

    element_id TEXT NOT NULL,
    group_id TEXT NOT NULL,
    visit TEXT,

    statistics JSON,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE gold.longitudinal IS '组别汇总统计 - longitudinal schema';
COMMENT ON COLUMN gold.longitudinal.element_id IS '参数代码：PHGA, VAS等';
COMMENT ON COLUMN gold.longitudinal.group_id IS '分组值：Drug, Placebo等';
COMMENT ON COLUMN gold.longitudinal.statistics IS '{"n": 48, "mean": 3.2, "sd": 1.1}';

CREATE INDEX IF NOT EXISTS idx_gold_long_deliverable ON gold.longitudinal(deliverable_id);
CREATE INDEX IF NOT EXISTS idx_gold_long_group ON gold.longitudinal(group_id);
CREATE INDEX IF NOT EXISTS idx_gold_long_element ON gold.longitudinal(element_id);
CREATE INDEX IF NOT EXISTS idx_gold_long_visit ON gold.longitudinal(visit);

-- ============================================================================
-- 3. gold.occurrence - Group-level occurrence statistics
-- ============================================================================
CREATE TABLE IF NOT EXISTS gold.occurrence (
    deliverable_id TEXT NOT NULL,

    element_id TEXT NOT NULL,
    group_id TEXT NOT NULL,
    selection TEXT,

    statistics JSON,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE gold.occurrence IS '组别汇总统计 - occurrence schema';
COMMENT ON COLUMN gold.occurrence.element_id IS '统计维度：term, coding_high, coding_low';
COMMENT ON COLUMN gold.occurrence.group_id IS '分组值：Drug, Placebo等';
COMMENT ON COLUMN gold.occurrence.selection IS '过滤条件：domain=AE;saefl=Y';
COMMENT ON COLUMN gold.occurrence.statistics IS '{"n_subjects": 10, "n_events": 15, "pct": 20.0}';

CREATE INDEX IF NOT EXISTS idx_gold_occ_deliverable ON gold.occurrence(deliverable_id);
CREATE INDEX IF NOT EXISTS idx_gold_occ_group ON gold.occurrence(group_id);
CREATE INDEX IF NOT EXISTS idx_gold_occ_element ON gold.occurrence(element_id);

-- ============================================================================
-- Helper View: Output statistics summary
-- ============================================================================
CREATE OR REPLACE VIEW gold.v_summary AS
SELECT 
    'baseline' AS schema,
    deliverable_id,
    COUNT(*) AS n_records
FROM gold.baseline
GROUP BY deliverable_id

UNION ALL

SELECT 
    'longitudinal' AS schema,
    deliverable_id,
    COUNT(*) AS n_records
FROM gold.longitudinal
GROUP BY deliverable_id

UNION ALL

SELECT 
    'occurrence' AS schema,
    deliverable_id,
    COUNT(*) AS n_records
FROM gold.occurrence
GROUP BY deliverable_id;

SELECT 'PRISM-DB Gold Schema v4.0 initialized. 3 tables created.' AS status;
