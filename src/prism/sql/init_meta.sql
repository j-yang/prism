-- ============================================================================
-- PRISM Meta Schema Initialization
-- Version: 5.1
-- Date: 2026-02-17
-- Description: Creates metadata tables for PRISM
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS meta;

-- ============================================================================
-- 1. meta.study_info - Study基本信息
-- ============================================================================
CREATE TABLE IF NOT EXISTS meta.study_info (
    studyid TEXT PRIMARY KEY,
    indication TEXT,
    description TEXT,
    als_version TEXT,
    spec_version TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE meta.study_info IS 'Study基本信息';

-- ============================================================================
-- 2. meta.params - Longitudinal参数定义
-- ============================================================================
CREATE TABLE IF NOT EXISTS meta.params (
    paramcd TEXT NOT NULL UNIQUE PRIMARY KEY,
    parameter TEXT NOT NULL,
    param_desc TEXT,

    category TEXT, -- 'Safety', 'Efficacy', 'PD'
    data_type TEXT,
    unit TEXT,

    default_source_form TEXT,
    default_source_var TEXT,
    default_aval_expr TEXT,

    has_baseline BOOLEAN DEFAULT TRUE,
    baseline_definition TEXT,

    is_external BOOLEAN DEFAULT FALSE,
    external_source TEXT,

    display_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE meta.params IS 'Longitudinal参数定义';

CREATE INDEX IF NOT EXISTS idx_params_paramcd ON meta.params(paramcd);
CREATE INDEX IF NOT EXISTS idx_params_category ON meta.params(category);

-- ============================================================================
-- 3. meta.attrs - Occurrence Domain扩展字段定义
-- ============================================================================
CREATE TABLE IF NOT EXISTS meta.attrs (
    domain TEXT PRIMARY KEY,
    fields JSON,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE meta.attrs IS 'Occurrence domain扩展字段定义';

-- ============================================================================
-- 4. meta.visits - Analysis Visit定义
-- ============================================================================
CREATE TABLE IF NOT EXISTS meta.visits (
    visit_id TEXT PRIMARY KEY,
    visitnum INTEGER,
    visit_name TEXT NOT NULL UNIQUE,
    visit_label TEXT,

    visit_type TEXT,
    is_baseline BOOLEAN DEFAULT FALSE,
    is_endpoint BOOLEAN DEFAULT FALSE,

    target_day INTEGER,
    window_lower INTEGER,
    window_upper INTEGER,

    display_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE meta.visits IS '分析用Visit定义';

CREATE INDEX IF NOT EXISTS idx_visits_visitnum ON meta.visits(visitnum);

-- ============================================================================
-- 5. meta.bronze_dictionary - Bronze层数据字典
-- ============================================================================
CREATE TABLE IF NOT EXISTS meta.bronze_dictionary (
    var_name TEXT NOT NULL,
    form_oid TEXT NOT NULL,
    field_oid TEXT,              -- EDC field标识，用于溯源
    schema TEXT NOT NULL,        -- 'baseline', 'longitudinal', 'occurrence'
    var_label TEXT,
    data_type TEXT,
    is_required BOOLEAN DEFAULT FALSE,
    codelist_ref TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (var_name, form_oid)
);

COMMENT ON TABLE meta.bronze_dictionary IS 'Bronze层数据字典（来自ALS解析）';
COMMENT ON COLUMN meta.bronze_dictionary.field_oid IS 'EDC系统中的Field OID，用于精确溯源';

CREATE INDEX IF NOT EXISTS idx_bronze_dictionary_form ON meta.bronze_dictionary(form_oid);
CREATE INDEX IF NOT EXISTS idx_bronze_dictionary_schema ON meta.bronze_dictionary(schema);

-- ============================================================================
-- 6. meta.silver_dictionary - Silver层数据字典
-- ============================================================================
CREATE TABLE IF NOT EXISTS meta.silver_dictionary (
    var_name TEXT PRIMARY KEY,
    var_label TEXT,
    schema TEXT NOT NULL,
    data_type TEXT,

    source_vars TEXT,
    transformation TEXT,
    transformation_type TEXT,
    rule_doc_path TEXT,
    description TEXT,

    param_ref TEXT,
    display_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE meta.silver_dictionary IS 'Silver层数据字典';

CREATE INDEX IF NOT EXISTS idx_silver_dictionary_schema ON meta.silver_dictionary(schema);
CREATE INDEX IF NOT EXISTS idx_silver_dictionary_param ON meta.silver_dictionary(param_ref);

-- ============================================================================
-- 7. meta.form_classification - Form分类映射
-- ============================================================================
CREATE TABLE IF NOT EXISTS meta.form_classification (
    form_oid TEXT PRIMARY KEY,
    domain TEXT,
    schema TEXT NOT NULL,
    source_forms TEXT,
    classification_confidence TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE meta.form_classification IS 'Form到Domain和Schema的映射';

CREATE INDEX IF NOT EXISTS idx_form_classification_domain ON meta.form_classification(domain);
CREATE INDEX IF NOT EXISTS idx_form_classification_schema ON meta.form_classification(schema);

-- ============================================================================
-- 8. meta.gold_dictionary - Gold层数据字典
-- ============================================================================
CREATE TABLE IF NOT EXISTS meta.gold_dictionary (
    element_id TEXT NOT NULL,
    group_id TEXT NOT NULL,
    schema TEXT NOT NULL,

    population TEXT,
    selection TEXT,

    statistics JSON,

    deliverable_id TEXT,

    description TEXT,
    unit TEXT,

    display_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (element_id, group_id, schema, COALESCE(selection, ''))
);

COMMENT ON TABLE meta.gold_dictionary IS 'Gold层数据字典（Group Level统计定义）';
COMMENT ON COLUMN meta.gold_dictionary.element_id IS '统计对象：variable名/paramcd/coding_high/coding_low';
COMMENT ON COLUMN meta.gold_dictionary.group_id IS '分组值：Drug, Placebo等';
COMMENT ON COLUMN meta.gold_dictionary.selection IS '过滤条件：visit=VISIT1, domain=AE;saefl=Y等';
COMMENT ON COLUMN meta.gold_dictionary.deliverable_id IS '服务于哪个 platinum 交付物';

CREATE INDEX IF NOT EXISTS idx_gold_dictionary_group ON meta.gold_dictionary(group_id);
CREATE INDEX IF NOT EXISTS idx_gold_dictionary_schema ON meta.gold_dictionary(schema);
CREATE INDEX IF NOT EXISTS idx_gold_dictionary_deliverable ON meta.gold_dictionary(deliverable_id);

-- ============================================================================
-- 9. meta.platinum_dictionary - Platinum交付物定义
-- ============================================================================
CREATE TABLE IF NOT EXISTS meta.platinum_dictionary (
    deliverable_id TEXT PRIMARY KEY,
    deliverable_type TEXT NOT NULL,

    title TEXT,

    schema TEXT,

    elements JSON,

    population TEXT,

    section TEXT,
    display_order INTEGER,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE meta.platinum_dictionary IS 'Platinum交付物定义（table/listing/figure）';
COMMENT ON COLUMN meta.platinum_dictionary.elements IS '[{"type": "variable|param|attr", "id": "age", "label": "Age"}, {"type": "attr", "id": "saefl", "filter": "saefl=''Y''"}]';

CREATE INDEX IF NOT EXISTS idx_platinum_dictionary_schema ON meta.platinum_dictionary(schema);
CREATE INDEX IF NOT EXISTS idx_platinum_dictionary_type ON meta.platinum_dictionary(deliverable_type);
CREATE INDEX IF NOT EXISTS idx_platinum_dictionary_section ON meta.platinum_dictionary(section);

-- ============================================================================
-- 10. meta.dependencies - 变量依赖关系
-- ============================================================================
CREATE TABLE IF NOT EXISTS meta.dependencies (
    from_var TEXT NOT NULL,
    to_var TEXT NOT NULL,

    PRIMARY KEY (from_var, to_var)
);

COMMENT ON TABLE meta.dependencies IS '变量依赖关系';

CREATE INDEX IF NOT EXISTS idx_dependencies_from ON meta.dependencies(from_var);
CREATE INDEX IF NOT EXISTS idx_dependencies_to ON meta.dependencies(to_var);

-- ============================================================================
-- Metadata Initialization Complete
-- ============================================================================

SELECT 'PRISM-DB Meta Schema v5.1 initialized. 10 tables created.' AS status;
