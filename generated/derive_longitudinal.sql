-- ============================================================================
-- PRISM-DB Silver Layer Derivation Script
-- Schema: longitudinal
-- Generated: 2026-02-14 00:22:29
-- ============================================================================

-- Ensure silver schema exists
CREATE SCHEMA IF NOT EXISTS silver;

-- Create base table if not exists
CREATE TABLE IF NOT EXISTS silver.longitudinal (
    usubjid TEXT PRIMARY KEY
);



-- [deriv_phga_chg] phga_chg (template: change_baseline)
SELECT 
    usubjid, 
    paramcd, 
    visitnum,
    aval,
    FIRST_VALUE(aval) OVER (PARTITION BY usubjid, paramcd ORDER BY visitnum) AS base,
    aval - FIRST_VALUE(aval) OVER (PARTITION BY usubjid, paramcd ORDER BY visitnum) AS phga_chg
FROM bronze.efficacy
WHERE paramcd IS NOT NULL;