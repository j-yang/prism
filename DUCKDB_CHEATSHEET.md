# DuckDB Cheatsheet for PRISM

## CLI Commands

```bash
# Open database
duckdb study.duckdb

# Open with description
duckdb study.duckdb -c "SHOW TABLES;"

# Execute SQL file
duckdb study.duckdb < query.sql

# Export to CSV
duckdb study.duckdb -c "COPY gold.baseline TO 'output.csv' (HEADER, DELIMITER ',');"

# Export to Parquet
duckdb study.duckdb -c "COPY gold.baseline TO 'output.parquet' (FORMAT PARQUET);"
```

## Schema Management

```sql
-- Create schema
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;
CREATE SCHEMA IF NOT EXISTS meta;

-- List schemas
SELECT schema_name FROM information_schema.schemata;

-- List tables in schema
SELECT table_name FROM information_schema.tables WHERE table_schema = 'meta';

-- Describe table
DESCRIBE meta.variables;
```

## Meta Schema Queries

```sql
-- Get all variables for a schema
SELECT var_id, var_name, var_label, data_type 
FROM meta.variables 
WHERE schema = 'baseline'
ORDER BY display_order;

-- Get derivations with complexity
SELECT deriv_id, target_var, transformation, complexity 
FROM meta.derivations 
ORDER BY complexity, deriv_id;

-- Get outputs by section
SELECT output_id, output_type, title 
FROM meta.outputs 
WHERE section = 'Efficacy'
ORDER BY display_order;

-- Get output with all variables
SELECT o.output_id, o.title, GROUP_CONCAT(ov.var_id) AS variables
FROM meta.outputs o
LEFT JOIN meta.output_variables ov ON o.output_id = ov.output_id
GROUP BY o.output_id, o.title;

-- Get missing derivations (variables without derivation rules)
SELECT v.var_id, v.var_name, v.schema
FROM meta.variables v
LEFT JOIN meta.derivations d ON v.var_id = d.target_var
WHERE d.deriv_id IS NULL;
```

## Bronze Layer

```sql
-- Import CSV to Bronze
CREATE TABLE bronze.demog AS 
SELECT * FROM read_csv_auto('raw/demog.csv');

-- Import SAS file
CREATE TABLE bronze.ae AS 
SELECT * FROM read_sas('raw/ae.sas7bdat');

-- Import Excel
CREATE TABLE bronze.labs AS 
SELECT * FROM read_excel('raw/labs.xlsx', sheet='Labs');

-- Sample data
SELECT * FROM bronze.demog USING SAMPLE 10%;
```

## Silver Layer

```sql
-- Create Silver baseline
CREATE TABLE IF NOT EXISTS silver.baseline AS
SELECT 
    usubjid,
    trta,
    age,
    sex,
    race
FROM bronze.demog;

-- Add column
ALTER TABLE silver.baseline ADD COLUMN agegrp TEXT;

-- Update with CASE
UPDATE silver.baseline
SET agegrp = CASE 
    WHEN age < 18 THEN '<18'
    WHEN age < 65 THEN '18-64'
    ELSE '>=65'
END;

-- Create index (DuckDB creates automatically, but explicit)
CREATE INDEX idx_baseline_usubjid ON silver.baseline(usubjid);
```

## Gold Layer

```sql
-- Descriptive stats by group
SELECT 
    trta,
    COUNT(*) as n,
    ROUND(AVG(age), 1) as mean,
    ROUND(STDDEV(age), 2) as sd,
    ROUND(MEDIAN(age), 1) as median,
    ROUND(MIN(age), 0) as min,
    ROUND(MAX(age), 0) as max
FROM silver.baseline
WHERE saffl = 'Y'
GROUP BY trta;

-- Categorical frequencies
SELECT 
    trta,
    sex,
    COUNT(*) as n,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY trta), 1) as pct
FROM silver.baseline
WHERE saffl = 'Y'
GROUP BY trta, sex;

-- Insert into Gold
INSERT INTO gold.baseline 
(output_id, group1_name, group1_value, variable, stat_name, stat_value, stat_display)
VALUES 
('T1_demog', 'TRTA', 'Drug A', 'AGE', 'mean', 45.2, '45.2'),
('T1_demog', 'TRTA', 'Drug A', 'AGE', 'sd', 12.3, '12.3');

-- Delete and re-insert (refresh)
DELETE FROM gold.baseline WHERE output_id = 'T1_demog';
```

## Useful Functions

```sql
-- Date handling
SELECT 
    CURRENT_DATE,
    DATE '2026-02-15',
    DATE_DIFF('day', trtsdt, astdt) as days_since_treatment;

-- String functions
SELECT 
    UPPER(sex) as sex_upper,
    LOWER(race) as race_lower,
    CONCAT(usubjid, '_', visit) as unique_id;

-- COALESCE
SELECT COALESCE(col1, col2, 'default') as result;

-- NULL handling
SELECT 
    COUNT(*) as total,
    COUNT(age) as non_null_age,
    COUNT(*) - COUNT(age) as null_age
FROM silver.baseline;

-- Type casting
SELECT 
    CAST(age AS VARCHAR) as age_str,
    CAST('2026-01-15' AS DATE) as date_val;
```

## Window Functions

```sql
-- Row number by group
SELECT 
    usubjid, visit, aval,
    ROW_NUMBER() OVER (PARTITION BY usubjid ORDER BY visit) as row_num
FROM silver.longitudinal;

-- First value (baseline)
SELECT 
    usubjid, paramcd, visit, aval,
    FIRST_VALUE(aval) OVER (PARTITION BY usubjid, paramcd ORDER BY visitnum) as base
FROM silver.longitudinal;

-- Change from baseline
SELECT 
    usubjid, paramcd, visit, aval,
    FIRST_VALUE(aval) OVER (PARTITION BY usubjid, paramcd ORDER BY visitnum) as base,
    aval - FIRST_VALUE(aval) OVER (PARTITION BY usubjid, paramcd ORDER BY visitnum) as chg
FROM silver.longitudinal;
```

## Export & Import

```sql
-- Export query result to CSV
COPY (SELECT * FROM gold.baseline WHERE output_id = 'T1_demog') 
TO 't1_demog.csv' (HEADER, DELIMITER ',');

-- Export to Parquet
COPY gold.baseline TO 'gold_baseline.parquet' (FORMAT PARQUET);

-- Export to JSON
COPY gold.baseline TO 'gold_baseline.json' (FORMAT JSON);

-- Import from Parquet
CREATE TABLE gold.new_table AS SELECT * FROM read_parquet('data.parquet');
```

## Database Management

```sql
-- Database info
PRAGMA database_size;
PRAGMA table_info('meta.variables');

-- Attach another database
ATTACH 'other.duckdb' AS other (READ_ONLY);

-- Query attached database
SELECT * FROM other.meta.variables;

-- Detach
DETACH other;

-- Vacuum (compact database)
VACUUM;
```

## Performance Tips

```sql
-- Use EXPLAIN to see query plan
EXPLAIN SELECT * FROM gold.baseline WHERE output_id = 'T1_demog';

-- Sample large tables first
SELECT * FROM silver.longitudinal USING SAMPLE 1%;

-- Use column pruning (only select needed columns)
SELECT usubjid, age FROM silver.baseline;  -- Good
SELECT * FROM silver.baseline;             -- Avoid
```

## Python Integration

```python
import duckdb

# Connect
conn = duckdb.connect('study.duckdb')

# Query to DataFrame
df = conn.execute("SELECT * FROM gold.baseline").df()

# Query to Arrow
arrow = conn.execute("SELECT * FROM gold.baseline").arrow()

# Register DataFrame as table
import pandas as pd
df = pd.DataFrame({'a': [1, 2, 3]})
conn.execute("CREATE TABLE temp AS SELECT * FROM df")

# Close
conn.close()
```

## Common PRISM Queries

```sql
-- Count subjects by treatment
SELECT trta, COUNT(DISTINCT usubjid) as n
FROM silver.baseline
WHERE saffl = 'Y'
GROUP BY trta;

-- List all Gold outputs
SELECT DISTINCT output_id, COUNT(*) as rows
FROM gold.baseline
GROUP BY output_id;

-- Quick data check
SELECT 
    'baseline' as layer,
    COUNT(*) as rows,
    COUNT(DISTINCT usubjid) as subjects
FROM silver.baseline
UNION ALL
SELECT 
    'longitudinal' as layer,
    COUNT(*) as rows,
    COUNT(DISTINCT usubjid) as subjects
FROM silver.longitudinal;
```
