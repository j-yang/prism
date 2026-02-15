-- ============================================================================
-- PRISM Meta Schema Initialization
-- Version: 3.0
-- Date: 2026-02-13
-- Description: Creates all 11 metadata tables for PRISM
-- Based on: ARCHITECTURE.md v3.1
-- ============================================================================

-- Create metadata schema
CREATE SCHEMA IF NOT EXISTS meta;

-- ============================================================================
-- 1. meta.study_info - Study基本信息
-- ============================================================================
CREATE TABLE IF NOT EXISTS meta.study_info (
    study_code TEXT PRIMARY KEY,
    indication TEXT,
    description TEXT,
    als_version TEXT,
    spec_version TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE meta.study_info IS 'Study基本信息，每个study.duckdb只有一行';

-- ============================================================================
-- 2. meta.params - 参数库 (可外链)
-- ============================================================================
CREATE TABLE IF NOT EXISTS meta.params (
    param_id TEXT PRIMARY KEY,           -- 'param_phga'
    paramcd TEXT NOT NULL UNIQUE,        -- 'PHGA'
    param_label TEXT NOT NULL,           -- 'Physician Global Activity'
    param_desc TEXT,
    
    category TEXT,                       -- 'efficacy', 'safety', 'pk', 'pd'
    data_type TEXT,                      -- 'continuous', 'categorical', 'ordinal'
    unit TEXT,                           -- 'cm', 'points', 'U/L'
    
    default_source_form TEXT,            -- 'QRS3'
    default_source_var TEXT,             -- 'QRS3RES'
    default_aval_expr TEXT,              -- How to derive AVAL
    
    has_baseline BOOLEAN DEFAULT TRUE,
    baseline_definition TEXT,            -- 'last non-missing before treatment'
    
    is_external BOOLEAN DEFAULT FALSE,   -- TRUE = 从外部库导入
    external_source TEXT,                -- 外部库路径或标识
    
    display_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE meta.params IS 'Longitudinal参数定义，可从外部库导入';

CREATE INDEX IF NOT EXISTS idx_params_paramcd ON meta.params(paramcd);
CREATE INDEX IF NOT EXISTS idx_params_category ON meta.params(category);
-- ============================================================================ 3. meta.flags - Flag库 (可外链) ============================================================================
CREATE TABLE IF NOT EXISTS meta.flags (
    flag_id TEXT PRIMARY KEY,            -- 'flag_teaefl'
    flag_name TEXT NOT NULL UNIQUE,      -- 'TEAEFL'
    flag_label TEXT NOT NULL,            -- 'Treatment-Emergent AE Flag'
    flag_desc TEXT,
    
    domain TEXT NOT NULL,                -- 'AE', 'CM', 'MH', 'ALL'
    
    default_condition TEXT,              -- SQL condition: "ASTDT >= TRTSDT"
    true_value TEXT DEFAULT 'Y',
    false_value TEXT DEFAULT 'N',
    
    is_external BOOLEAN DEFAULT FALSE,
    external_source TEXT,
    
    display_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE meta.flags IS 'Occurrence事件标志定义，可从外部库导入';

CREATE INDEX IF NOT EXISTS idx_flags_domain ON meta.flags(domain);

-- ============================================================================
-- 4. meta.visits - Analysis Visit库
-- ============================================================================
CREATE TABLE IF NOT EXISTS meta.visits (
    visit_id TEXT PRIMARY KEY,           -- 'visit_baseline'
    visitnum INTEGER,                    -- 0, 1, 2, 3...
    visit_name TEXT NOT NULL UNIQUE,     -- 'BASELINE', 'DAY28', 'WEEK12'
    visit_label TEXT,                    -- 'Baseline', 'Day 28', 'Week 12'
    
    visit_type TEXT,                     -- 'scheduled', 'unscheduled', 'early_term'
    is_baseline BOOLEAN DEFAULT FALSE,
    is_endpoint BOOLEAN DEFAULT FALSE,
    
    target_day INTEGER,                  -- 目标天数: 0, 28, 84
    window_lower INTEGER,                -- 窗口下限: -3
    window_upper INTEGER,                -- 窗口上限: +3
    
    is_external BOOLEAN DEFAULT FALSE,
    external_source TEXT,
    
    display_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE meta.visits IS '分析用Visit定义';

CREATE INDEX IF NOT EXISTS idx_visits_visitnum ON meta.visits(visitnum);

-- ============================================================================
-- 5. meta.variables - 变量表
-- ============================================================================
CREATE TABLE IF NOT EXISTS meta.variables (
    var_id TEXT PRIMARY KEY,             -- 'age', 'trtsdt', 'phga_bl'
    var_name TEXT NOT NULL,
    var_label TEXT,
    
    schema TEXT NOT NULL,                -- 'baseline', 'longitudinal', 'occurrence'
    block TEXT,                          -- 'COMMON', 'BASELINE', 'FLAGS'
    data_type TEXT,                      -- 'numeric', 'character', 'date', 'flag'
    
    param_ref TEXT,                      -- FK → meta.params.paramcd (for longitudinal)
    flag_ref TEXT,                       -- FK → meta.flags.flag_name (for occurrence)
    
    is_baseline_of_param BOOLEAN DEFAULT FALSE,
    
    display_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE meta.variables IS '统一的变量注册表';

CREATE INDEX IF NOT EXISTS idx_variables_schema ON meta.variables(schema);
CREATE INDEX IF NOT EXISTS idx_variables_block ON meta.variables(block);
CREATE INDEX IF NOT EXISTS idx_variables_param_ref ON meta.variables(param_ref);
CREATE INDEX IF NOT EXISTS idx_variables_flag_ref ON meta.variables(flag_ref);

-- ============================================================================
-- 6. meta.derivations - 衍生规则
-- ============================================================================
CREATE TABLE IF NOT EXISTS meta.derivations (
    deriv_id TEXT PRIMARY KEY,
    target_var TEXT NOT NULL UNIQUE,     -- FK → meta.variables.var_id
    
    source_vars TEXT,                    -- JSON: dependent variables
    source_tables TEXT,                  -- JSON: bronze tables
    
    transformation TEXT NOT NULL,        -- SQL or pseudo-code
    transformation_type TEXT,            -- 'direct', 'sql', 'function', 'rule_doc'
    
    function_id TEXT,                    -- FK → meta.functions
    rule_doc_path TEXT,
    
    complexity TEXT,                     -- 'simple', 'medium', 'complex'
    description TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE meta.derivations IS '变量/参数的衍生规则';

CREATE INDEX IF NOT EXISTS idx_derivations_target_var ON meta.derivations(target_var);
CREATE INDEX IF NOT EXISTS idx_derivations_complexity ON meta.derivations(complexity);

-- ============================================================================
-- 7. meta.outputs - 输出定义
-- ============================================================================
CREATE TABLE IF NOT EXISTS meta.outputs (
    output_id TEXT PRIMARY KEY,          -- 'T1_demog', 'F1_phga'
    output_type TEXT NOT NULL,           -- 'table', 'listing', 'figure'
    title TEXT,
    
    schema TEXT NOT NULL,                -- 'baseline', 'longitudinal', 'occurrence'
    source_block TEXT,
    
    population TEXT,                     -- 'SAFFL', 'FASFL'
    visit_filter TEXT,                   -- list of visits
    filter_expr TEXT,
    
    render_function TEXT,
    render_options TEXT,                 -- JSON
    
    section TEXT,
    display_order INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE meta.outputs IS '输出定义（table/listing/figure）';

CREATE INDEX IF NOT EXISTS idx_outputs_schema ON meta.outputs(schema);
CREATE INDEX IF NOT EXISTS idx_outputs_section ON meta.outputs(section);

-- ============================================================================
-- 8. meta.output_variables - 输出-变量关联
-- ============================================================================
CREATE TABLE IF NOT EXISTS meta.output_variables (
    output_id TEXT NOT NULL,
    var_id TEXT NOT NULL,
    
    role TEXT,                           -- 'group', 'measure', 'filter', 'display'
    display_label TEXT,
    display_order INTEGER,
    
    PRIMARY KEY (output_id, var_id)
);

COMMENT ON TABLE meta.output_variables IS '输出需要的变量';

CREATE INDEX IF NOT EXISTS idx_output_variables_output ON meta.output_variables(output_id);
CREATE INDEX IF NOT EXISTS idx_output_variables_var ON meta.output_variables(var_id);

-- ============================================================================
-- 9. meta.output_params - 输出-参数关联
-- ============================================================================
CREATE TABLE IF NOT EXISTS meta.output_params (
    output_id TEXT NOT NULL,
    paramcd TEXT NOT NULL,
    
    display_order INTEGER,
    
    PRIMARY KEY (output_id, paramcd)
);

COMMENT ON TABLE meta.output_params IS '输出需要的参数（longitudinal）';

CREATE INDEX IF NOT EXISTS idx_output_params_output ON meta.output_params(output_id);
CREATE INDEX IF NOT EXISTS idx_output_params_paramcd ON meta.output_params(paramcd);

-- ============================================================================
-- 10. meta.functions - 函数库
-- ============================================================================
CREATE TABLE IF NOT EXISTS meta.functions (
    function_id TEXT PRIMARY KEY,
    function_name TEXT NOT NULL,
    description TEXT,
    
    impl_type TEXT NOT NULL,             -- 'sql', 'r', 'python'
    impl_code TEXT,
    
    input_params TEXT,                   -- JSON
    output_type TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE meta.functions IS '复杂函数/计算逻辑';

-- ============================================================================
-- 11. meta.dependencies - 依赖关系
-- ============================================================================
CREATE TABLE IF NOT EXISTS meta.dependencies (
    from_var TEXT NOT NULL,
    to_var TEXT NOT NULL,
    
    PRIMARY KEY (from_var, to_var)
);

COMMENT ON TABLE meta.dependencies IS '变量间的依赖关系（用于拓扑排序）';

CREATE INDEX IF NOT EXISTS idx_dependencies_from ON meta.dependencies(from_var);
CREATE INDEX IF NOT EXISTS idx_dependencies_to ON meta.dependencies(to_var);

-- ============================================================================
-- 12. meta.form_classification - Form分类映射
-- ============================================================================
CREATE TABLE IF NOT EXISTS meta.form_classification (
    form_oid TEXT PRIMARY KEY,         -- 'AE', 'CM1', 'MH2'
    domain TEXT,                       -- 'AE', 'CM', 'MH', 'DEATH'
    schema TEXT NOT NULL,              -- 'baseline', 'longitudinal', 'occurrence'
    source_forms TEXT,                 -- JSON: 合并的原始 forms
    classification_confidence TEXT,    -- 'high', 'medium', 'low'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE meta.form_classification IS 'Form到Domain和Schema的映射关系';

CREATE INDEX IF NOT EXISTS idx_form_classification_domain ON meta.form_classification(domain);
CREATE INDEX IF NOT EXISTS idx_form_classification_schema ON meta.form_classification(schema);

-- ============================================================================
-- Helper Views
-- ============================================================================

-- View: 所有变量及其衍生状态
CREATE OR REPLACE VIEW meta.v_variables_with_derivations AS
SELECT 
    v.var_id,
    v.var_name,
    v.var_label,
    v.schema,
    v.block,
    v.data_type,
    v.param_ref,
    v.flag_ref,
    d.deriv_id,
    d.transformation_type,
    d.complexity
FROM meta.variables v
LEFT JOIN meta.derivations d ON v.var_id = d.target_var;

-- View: 输出汇总
CREATE OR REPLACE VIEW meta.v_outputs_summary AS
SELECT 
    o.output_id,
    o.output_type,
    o.schema,
    o.title,
    o.section,
    COUNT(DISTINCT ov.var_id) AS num_variables,
    COUNT(DISTINCT op.paramcd) AS num_params
FROM meta.outputs o
LEFT JOIN meta.output_variables ov ON o.output_id = ov.output_id
LEFT JOIN meta.output_params op ON o.output_id = op.output_id
GROUP BY o.output_id, o.output_type, o.schema, o.title, o.section;

-- ============================================================================
-- Metadata Initialization Complete
-- ============================================================================

SELECT 'PRISM-DB Meta Schema v3.1 initialized successfully. 11 tables created.' AS status;
