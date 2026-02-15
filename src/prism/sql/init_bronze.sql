-- ============================================================================
-- PRISM Bronze Schema Initialization
-- Version: 1.0
-- Description: Creates Bronze layer tables for raw data storage
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS bronze;

-- ============================================================================
-- 1. bronze.baseline - 基线数据 (每个受试者一条记录)
-- ============================================================================
CREATE TABLE IF NOT EXISTS bronze.baseline (
    usubjid TEXT NOT NULL,
    subjid TEXT,
    attrs JSON,
    PRIMARY KEY (usubjid)
);

COMMENT ON TABLE bronze.baseline IS '基线数据，每个受试者一条记录';

-- ============================================================================
-- 2. bronze.longitudinal - 纵向数据 (每个受试者每个 visit 一条记录)
-- ============================================================================
CREATE TABLE IF NOT EXISTS bronze.longitudinal (
    usubjid TEXT NOT NULL,
    subjid TEXT,
    visit_id TEXT NOT NULL,
    attrs JSON,
    PRIMARY KEY (usubjid, visit_id)
);

COMMENT ON TABLE bronze.longitudinal IS '纵向数据，每个受试者每个 visit 一条记录';

CREATE INDEX IF NOT EXISTS idx_longitudinal_visit ON bronze.longitudinal(visit_id);

-- ============================================================================
-- 3. bronze.occurrence - 事件数据 (每个事件一条记录)
-- ============================================================================
CREATE TABLE IF NOT EXISTS bronze.occurrence (
    usubjid TEXT NOT NULL,
    subjid TEXT,
    domain TEXT NOT NULL,
    seq INTEGER NOT NULL,
    term TEXT,
    startdt DATE,
    enddt DATE,
    coding_high TEXT,
    coding_low TEXT,
    attrs JSON,
    PRIMARY KEY (usubjid, domain, seq)
);

COMMENT ON TABLE bronze.occurrence IS '事件数据，合并 AE/CM/MH/PR/DEATH 等 domain';

CREATE INDEX IF NOT EXISTS idx_occurrence_domain ON bronze.occurrence(domain);
CREATE INDEX IF NOT EXISTS idx_occurrence_startdt ON bronze.occurrence(startdt);
CREATE INDEX IF NOT EXISTS idx_occurrence_coding_high ON bronze.occurrence(coding_high);
CREATE INDEX IF NOT EXISTS idx_occurrence_coding_low ON bronze.occurrence(coding_low);

-- ============================================================================
-- Bronze Schema Initialized
-- ============================================================================

SELECT 'PRISM Bronze Schema initialized. 3 tables created.' AS status;
