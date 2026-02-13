-- ============================================================================
-- PRISM-DB Silver Layer Derivation Script
-- Schema: occurrence
-- Generated: 2026-02-14 00:22:29
-- ============================================================================

-- Ensure silver schema exists
CREATE SCHEMA IF NOT EXISTS silver;

-- Create base table if not exists
CREATE TABLE IF NOT EXISTS silver.occurrence (
    usubjid TEXT PRIMARY KEY
);



-- [deriv_teaefl] teaefl (template: date_min)
SELECT usubjid, MIN(aestdtc) AS teaefl
FROM bronze.ae
WHERE 1=1
GROUP BY usubjid;