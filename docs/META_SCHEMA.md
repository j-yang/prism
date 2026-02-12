# PRISM-DB Meta Schema v2

**设计原则**: 单Study数据库 + 规范化 + Agent友好

---

## 双层设计：DDL + Python Models

Meta Schema同时存在于两个层次：

```
┌─────────────────────────────────────────────────────────────────────┐
│  Layer 1: Database DDL                                              │
│  ├── sql/init_meta.sql                                              │
│  └── 执行后在 study.duckdb 中创建 meta.* 表                          │
│                                                                      │
│  Layer 2: Python Models                                             │
│  ├── src/prismdb/schema/models.py                                   │
│  └── Pydantic/dataclass，用于Agent解析和代码生成                     │
└─────────────────────────────────────────────────────────────────────┘
```

### DDL ↔ Python Model 对应关系

| Meta表 | Python Model | 用途 |
|--------|--------------|------|
| `meta.study_info` | `StudyInfo` | 研究基本信息 |
| `meta.variables` | `Variable` | 变量定义 |
| `meta.derivations` | `Derivation` | 衍生规则 |
| `meta.params` | `Parameter` | 参数库 |
| `meta.flags` | `Flag` | Flag库 |
| `meta.visits` | `Visit` | 访视定义 |
| `meta.outputs` | `Output` | 输出定义 |
| `meta.output_variables` | `OutputVariable` | 输出-变量关联 |
| `meta.output_params` | `OutputParam` | 输出-参数关联 |
| `meta.functions` | `Function` | 函数库 |
| `meta.dependencies` | `Dependency` | 依赖图 |

### 为什么需要两层？

```
Excel Spec                    Python Models                 DuckDB
────────────────────────────────────────────────────────────────────
                    parse                      load
centralized_spec.xlsx ───→ List[Variable] ───→ meta.variables
                              │
                              │ Agent读取
                              ↓
                        生成 derive_silver.sql
```

1. **解析器输出** - 把Excel解析成结构化对象
2. **Agent输入** - Agent理解spec的数据结构
3. **验证** - 类型检查、必填字段检查
4. **代码生成** - 基于model生成SQL/R代码

---

## 架构前提

```
study_A.db          study_B.db          study_C.db
├── meta.*          ├── meta.*          ├── meta.*
├── bronze.*        ├── bronze.*        ├── bronze.*
├── silver.*        ├── silver.*        ├── silver.*
└── gold.*          └── gold.*          └── gold.*
```

- **每个study一个独立的db文件**
- **meta是db的一部分**，描述这个study的元数据
- **跨study共享在spec文件层面**（Excel），import时各自导入
- **不需要study_code区分**，因为整个db就是一个study

---

## 核心实体

### 实体1: Variable（变量）
- 一个数据点的定义
- schema区分粒度：baseline/longitudinal/occurrence

### 实体2: Derivation（衍生规则）
- 如何从源数据计算出目标变量
- 一个变量一条衍生规则

### 实体3: Output（输出）
- 数据的展示需求
- 一个output需要若干变量

---

## 规范化Schema设计

### 设计理念

```
参考库 (可外链/跨study共享)        Study-specific
├── meta.params                    ├── meta.study_info
├── meta.flags                     ├── meta.variables
└── meta.visits                    ├── meta.derivations
                                   ├── meta.outputs
                                   └── ...
```

- **params/flags/visits**: 知识库性质，可以从外部库导入或本地定义
- **variables/derivations**: study-specific，但可以引用params/flags

---

### 1. meta.study_info

**当前study的基本信息**

```sql
CREATE TABLE meta.study_info (
    study_code TEXT PRIMARY KEY,
    indication TEXT,
    description TEXT,
    als_version TEXT,
    spec_version TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

### 2. meta.params (参数库)

**Longitudinal参数定义** - 可外链

```sql
CREATE TABLE meta.params (
    param_id TEXT PRIMARY KEY,           -- 'param_phga'
    paramcd TEXT NOT NULL UNIQUE,        -- 'PHGA'
    param_label TEXT NOT NULL,           -- 'Physician Global Activity'
    param_desc TEXT,                     -- 详细描述
    
    -- 参数特性
    category TEXT,                       -- 'efficacy', 'safety', 'pk', 'pd'
    data_type TEXT,                      -- 'continuous', 'categorical', 'ordinal'
    unit TEXT,                           -- 'cm', 'points', 'U/L'
    
    -- 来源信息 (默认值，可被study override)
    default_source_form TEXT,            -- 'QRS3'
    default_source_var TEXT,             -- 'QRS3RES'
    default_aval_expr TEXT,              -- How to derive AVAL
    
    -- Baseline handling
    has_baseline BOOLEAN DEFAULT TRUE,
    baseline_definition TEXT,            -- 'last non-missing before treatment'
    
    -- 外链标记
    is_external BOOLEAN DEFAULT FALSE,   -- TRUE = 从外部库导入
    external_source TEXT,                -- 外部库路径或标识
    
    display_order INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

### 3. meta.flags (Flag库)

**Occurrence事件标志定义** - 可外链

```sql
CREATE TABLE meta.flags (
    flag_id TEXT PRIMARY KEY,            -- 'flag_teaefl'
    flag_name TEXT NOT NULL,             -- 'TEAEFL'
    flag_label TEXT NOT NULL,            -- 'Treatment-Emergent AE Flag'
    flag_desc TEXT,
    
    -- 适用范围
    domain TEXT NOT NULL,                -- 'AE', 'CM', 'MH', 'ALL'
    
    -- 标志逻辑 (默认值)
    default_condition TEXT,              -- SQL condition: "ASTDT >= TRTSDT"
    true_value TEXT DEFAULT 'Y',
    false_value TEXT DEFAULT 'N',
    
    -- 外链标记
    is_external BOOLEAN DEFAULT FALSE,
    external_source TEXT,
    
    display_order INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

### 4. meta.visits (Analysis Visit库)

**分析用Visit定义**

```sql
CREATE TABLE meta.visits (
    visit_id TEXT PRIMARY KEY,           -- 'visit_baseline'
    visitnum INTEGER,                    -- 0, 1, 2, 3...
    visit_name TEXT NOT NULL,            -- 'BASELINE', 'DAY28', 'WEEK12'
    visit_label TEXT,                    -- 'Baseline', 'Day 28', 'Week 12'
    
    -- Visit特性
    visit_type TEXT,                     -- 'scheduled', 'unscheduled', 'early_term'
    is_baseline BOOLEAN DEFAULT FALSE,
    is_endpoint BOOLEAN DEFAULT FALSE,
    
    -- 时间窗口
    target_day INTEGER,                  -- 目标天数: 0, 28, 84
    window_lower INTEGER,                -- 窗口下限: -3
    window_upper INTEGER,                -- 窗口上限: +3
    
    -- 外链标记
    is_external BOOLEAN DEFAULT FALSE,
    external_source TEXT,
    
    display_order INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

### 5. meta.variables (变量表)

**Baseline变量 + 对params/flags的引用**

```sql
CREATE TABLE meta.variables (
    var_id TEXT PRIMARY KEY,             -- 'age', 'trtsdt', 'phga_bl'
    var_name TEXT NOT NULL,
    var_label TEXT,
    
    -- 变量类型
    schema TEXT NOT NULL,                -- 'baseline', 'longitudinal', 'occurrence'
    block TEXT,                          -- 'COMMON', 'BASELINE', 'FLAGS'
    data_type TEXT,                      -- 'numeric', 'character', 'date', 'flag'
    
    -- 外链引用 (互斥)
    param_ref TEXT,                      -- FK → meta.params.paramcd (for longitudinal)
    flag_ref TEXT,                       -- FK → meta.flags.flag_name (for occurrence)
    
    -- 用于baseline derived from param (如 PHGA_BL)
    is_baseline_of_param BOOLEAN DEFAULT FALSE,
    
    display_order INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_var_schema ON meta.variables(schema);
CREATE INDEX idx_var_param ON meta.variables(param_ref);
CREATE INDEX idx_var_flag ON meta.variables(flag_ref);
```

---

### 6. meta.derivations (衍生规则)

```sql
CREATE TABLE meta.derivations (
    deriv_id TEXT PRIMARY KEY,
    target_var TEXT NOT NULL UNIQUE,     -- FK → meta.variables.var_id
    
    -- Source
    source_vars TEXT,                    -- JSON: dependent variables
    source_tables TEXT,                  -- JSON: bronze tables
    
    -- Transformation
    transformation TEXT NOT NULL,        -- SQL or pseudo-code
    transformation_type TEXT,            -- 'direct', 'sql', 'function', 'rule_doc'
    
    -- For complex
    function_id TEXT,                    -- FK → meta.functions
    rule_doc_path TEXT,
    
    complexity TEXT,                     -- 'simple', 'medium', 'complex'
    description TEXT,
    
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

### 7. meta.outputs

```sql
CREATE TABLE meta.outputs (
    output_id TEXT PRIMARY KEY,          -- 'T1_demog', 'F1_phga'
    output_type TEXT NOT NULL,           -- 'table', 'listing', 'figure'
    title TEXT,
    
    schema TEXT NOT NULL,                -- 'baseline', 'longitudinal', 'occurrence'
    source_block TEXT,
    
    -- Analysis settings
    population TEXT,                     -- 'SAFFL', 'FASFL'
    visit_filter TEXT,                   -- FK or list → meta.visits
    filter_expr TEXT,
    
    -- Rendering
    render_function TEXT,
    render_options TEXT,                 -- JSON
    
    section TEXT,
    display_order INTEGER,
    
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

### 8. meta.output_variables

```sql
CREATE TABLE meta.output_variables (
    id INTEGER PRIMARY KEY,
    output_id TEXT NOT NULL,
    var_id TEXT NOT NULL,
    
    role TEXT,                           -- 'group', 'measure', 'filter', 'display'
    display_label TEXT,
    display_order INTEGER,
    
    UNIQUE(output_id, var_id)
);
```

---

### 9. meta.output_params

**输出需要哪些参数** (for longitudinal outputs)

```sql
CREATE TABLE meta.output_params (
    id INTEGER PRIMARY KEY,
    output_id TEXT NOT NULL,
    paramcd TEXT NOT NULL,               -- FK → meta.params
    
    display_order INTEGER,
    
    UNIQUE(output_id, paramcd)
);
```

---

### 10. meta.functions

```sql
CREATE TABLE meta.functions (
    function_id TEXT PRIMARY KEY,
    function_name TEXT NOT NULL,
    description TEXT,
    
    impl_type TEXT NOT NULL,             -- 'sql', 'r', 'python'
    impl_code TEXT,
    
    input_params TEXT,                   -- JSON
    output_type TEXT,
    
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

### 11. meta.dependencies

```sql
CREATE TABLE meta.dependencies (
    id INTEGER PRIMARY KEY,
    from_var TEXT NOT NULL,
    to_var TEXT NOT NULL,
    
    UNIQUE(from_var, to_var)
);
```

---

## ER Diagram

```
┌─────────────────────────────────────────────────────────┐
│           参考库 (可外链/跨study共享)                      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │
│  │ meta.params  │ │ meta.flags   │ │ meta.visits  │    │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘    │
└─────────┼────────────────┼────────────────┼────────────┘
          │ ref            │ ref            │ ref
          ↓                ↓                ↓
┌─────────────────┐     ┌─────────────────┐
│  meta.variables │←────│meta.derivations │
└────────┬────────┘     └─────────────────┘
         │
         ↓
┌─────────────────┐     ┌─────────────────┐
│meta.output_vars │────→│  meta.outputs   │←── meta.output_params
└─────────────────┘     └─────────────────┘
         
┌─────────────────┐     ┌─────────────────┐
│meta.dependencies│     │  meta.functions │
└─────────────────┘     └─────────────────┘

┌─────────────────┐
│ meta.study_info │ (1 row)
└─────────────────┘
```

**表数量**: 11张

---

## 外链机制

### 参考库的外链

```
global_params.json (全局参数库)
        │
        ├──→ import (is_external=TRUE) ──→ study_A.db/meta.params
        └──→ import (is_external=TRUE) ──→ study_B.db/meta.params

study_specific params:
        └──→ insert (is_external=FALSE) ──→ study_A.db/meta.params
```

- `is_external = TRUE`: 从外部库导入，不应修改
- `is_external = FALSE`: study自定义，可以修改
- `external_source`: 记录来源，便于追踪

### Visit库的使用

```sql
-- 定义标准visit
INSERT INTO meta.visits VALUES 
('v_bl', 0, 'BASELINE', 'Baseline', 'scheduled', TRUE, FALSE, 0, -7, 1),
('v_d28', 1, 'DAY28', 'Day 28', 'scheduled', FALSE, FALSE, 28, -3, 3),
('v_d56', 2, 'DAY56', 'Day 56', 'scheduled', FALSE, FALSE, 56, -3, 3),
...

-- Output可以指定visit范围
SELECT * FROM meta.outputs WHERE visit_filter = 'BASELINE,DAY28,DAY56';
```

---

## Agent使用场景

### 场景1: 获取所有变量

```sql
SELECT var_id, var_name, schema, block, data_type
FROM meta.variables
ORDER BY schema, block, display_order;
```

### 场景2: 获取变量的衍生规则

```sql
SELECT v.var_name, d.transformation, d.transformation_type, d.complexity
FROM meta.variables v
JOIN meta.derivations d ON v.var_id = d.target_var
WHERE v.var_id = 'trtsdt';
```

### 场景3: 获取输出需要的变量

```sql
SELECT 
    o.output_id,
    o.output_type,
    v.var_name,
    ov.role,
    d.transformation
FROM meta.outputs o
JOIN meta.output_variables ov ON o.output_id = ov.output_id
JOIN meta.variables v ON ov.var_id = v.var_id
LEFT JOIN meta.derivations d ON v.var_id = d.target_var
WHERE o.output_id = 'T1_demog'
ORDER BY ov.display_order;
```

### 场景4: 按依赖顺序执行衍生

```sql
-- 拓扑排序：找出执行顺序
WITH RECURSIVE exec_order AS (
    -- Level 0: 没有依赖的变量
    SELECT v.var_id, 0 AS level
    FROM meta.variables v
    WHERE NOT EXISTS (
        SELECT 1 FROM meta.dependencies d WHERE d.from_var = v.var_id
    )
    
    UNION ALL
    
    -- Level N+1: 依赖Level N变量的变量
    SELECT d.from_var, e.level + 1
    FROM meta.dependencies d
    JOIN exec_order e ON d.to_var = e.var_id
)
SELECT var_id, MAX(level) AS exec_level
FROM exec_order
GROUP BY var_id
ORDER BY exec_level;
```

### 场景5: 找出缺少衍生规则的变量

```sql
SELECT v.var_id, v.var_name, v.schema
FROM meta.variables v
LEFT JOIN meta.derivations d ON v.var_id = d.target_var
WHERE d.deriv_id IS NULL;
```

---

## 跨Study共享机制

```
centralized_spec.xlsx (共享定义)
        │
        ├──→ parser ──→ study_A.db/meta.*
        │
        ├──→ parser ──→ study_B.db/meta.*
        │
        └──→ parser ──→ study_C.db/meta.*
```

- **共享发生在spec文件层面**
- 每个study.db是完整独立的
- Parser负责从spec提取该study需要的部分

---

## 与Bronze/Silver/Gold的关系

```
meta.variables      →  silver.baseline (columns)
                    →  silver.longitudinal (PARAMCD values)
                    →  silver.occurrence (columns)

meta.derivations    →  bronze → silver transformation SQL

meta.outputs        →  silver → gold aggregation
                    →  gold → platinum rendering
```

---

*设计版本: 2.0*
*日期: 2026-02-12*
