-- ============================================================================
-- PRISM-DB Silver Layer Derivation Script
-- Schema: baseline
-- Generated: 2026-02-14 00:22:25
-- ============================================================================

-- Ensure silver schema exists
CREATE SCHEMA IF NOT EXISTS silver;

-- Create base table if not exists
CREATE TABLE IF NOT EXISTS silver.baseline (
    usubjid TEXT PRIMARY KEY
);



-- [deriv_agegrp] agegrp (template: age_group)
ALTER TABLE silver.baseline ADD COLUMN IF NOT EXISTS agegrp TEXT;
UPDATE silver.baseline
SET agegrp = CASE 
    WHEN age < 18 THEN '<18'
    WHEN age < 65 THEN '18-64'
    ELSE '>=65'
END;

-- [deriv_trtsdt] trtsdt (method: llm)
-- Complexity: simple
-- ⚠️ NEEDS REVIEW: LLM generated, please verify
-- Rule: MIN(EXSTDT) where EXDOSE > 0...
-- 生成目标变量: First Treatment Date (trtsdt)
INSERT INTO baseline (usubjid, trtsdt)
SELECT 
    usubjid,
    MIN(exstdt) AS trtsdt
FROM bronze.ex
WHERE exdose > 0
GROUP BY usubjid
ON CONFLICT (usubjid) 
DO UPDATE SET 
    trtsdt = EXCLUDED.trtsdt;