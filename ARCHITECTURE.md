# PRISM-DB - 架构设计文档 v3.1

**更新日期**: 2026-02-12  
**状态**: 架构设计最终确认  
**项目定位**: Clinical Trial Data Warehouse + Code Generation Agent

---

## 项目定位

**PRISM-DB** 是一个临床试验数据处理框架，包含：
1. **数据仓库** - Bronze/Silver/Gold三层Medallion架构
2. **元数据驱动** - Schema、衍生规则、输出定义都在meta表中
3. **Code Generation Agent** - 基于metadata生成SQL/R/Python代码

### 核心理念：Agent是Code Generator，不是Executor

```
┌────────────────────────────────────────────────────────────────┐
│                                                                 │
│   ┌─────────────┐         ┌─────────────────────────────────┐  │
│   │   Inputs    │         │         Agent (Code Gen)        │  │
│   │             │ ──────→ │                                 │  │
│   │ • ALS       │         │  • 理解输入                      │  │
│   │ • Spec      │         │  • 理解meta schema              │  │
│   │ • Rule Docs │         │  • 生成代码                      │  │
│   │ • Meta.*    │         │                                 │  │
│   └─────────────┘         └──────────────┬──────────────────┘  │
│                                          │                      │
│                                          │ 生成                 │
│                                          ↓                      │
│                           ┌─────────────────────────────────┐  │
│                           │      Generated Code             │  │
│                           │                                 │  │
│                           │  • 01_init_bronze.py            │  │
│                           │  • 02_derive_silver.sql         │  │
│                           │  • 03_compute_gold.R            │  │
│                           │  • 04_render_platinum.R         │  │
│                           └──────────────┬──────────────────┘  │
│                                          │                      │
│                                          │ 用户执行              │
│                                          ↓                      │
│                           ┌─────────────────────────────────┐  │
│                           │         study.duckdb            │  │
│                           │  Bronze → Silver → Gold         │  │
│                           └─────────────────────────────────┘  │
│                                          │                      │
│                                          ↓                      │
│                           ┌─────────────────────────────────┐  │
│                           │         outputs/                │  │
│                           │  *.pptx, *.rtf, *.png           │  │
│                           └─────────────────────────────────┘  │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

**Agent的本质**:

| Agent 不是 | Agent 是 |
|------------|----------|
| Runtime executor | **Code generator** |
| 接触真实数据 | **只读metadata/spec** |
| 端到端自动化 | **辅助编程** |
| 黑盒 | **生成可审查的代码** |

**类似于**: GitHub Copilot、dbt codegen、Cursor

---

## 双层Schema设计

Meta Schema同时存在于两个层次：

| Layer | 位置 | 用途 |
|-------|------|------|
| **DDL** | `sql/init_meta.sql` | 数据库表定义 |
| **Python Models** | `src/prismdb/schema/models.py` | Agent解析/验证/代码生成 |

详见 [docs/META_SCHEMA.md](docs/META_SCHEMA.md)

---

## 目录

- [一、核心架构](#一核心架构)
- [二、数据层详细设计](#二数据层详细设计)
- [三、Metadata详细设计](#三metadata-详细设计)
- [四、ETL工作流程](#四etl工作流程)
- [五、为什么选择DuckDB](#五为什么选择duckdb)
- [六、数据访问模式](#六数据访问模式)
- [附录：术语对照](#附录术语对照)

---

## 一、核心架构

### 1.1 三层数据仓库架构 (Medallion Architecture)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          study.duckdb (DuckDB数据库)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ Bronze Layer (Raw Data)                                                │ │
│  │ 原始EDC数据，保持form原始结构                                            │ │
│  │ ┌──────────────┐ ┌────────────────────┐ ┌────────────────────┐         │ │
│  │ │ bronze.demog │ │ bronze.vs          │ │ bronze.ae          │         │ │
│  │ │ bronze.mh    │ │ bronze.labs        │ │ bronze.cm          │ ...     │ │
│  │ └──────────────┘ └────────────────────┘ └────────────────────┘         │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                        │
│                                    ▼                                        │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ Silver Layer (Subject Level - Analysis Ready)                          │ │
│  │ 受试者粒度，分三种schema                                                 │ │
│  │ ┌────────────────┐ ┌────────────────────┐ ┌────────────────────┐       │ │
│  │ │ silver.baseline│ │ silver.longitudinal│ │ silver.occurrence  │       │ │
│  │ │ 1 row/subject  │ │ 1 row/subj×para×vis│ │ 1 row/event        │       │ │
│  │ │ +衍生变量      │ │ +BASE/CHG/Flag     │ │ +事件分类flag      │       │ │
│  │ └────────────────┘ └────────────────────┘ └────────────────────┘       │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                        │
│                                    ▼                                        │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ Gold Layer (Group Level - Aggregated Statistics)                       │ │
│  │ 组别汇总统计量，长表结构                                                 │ │
│  │ ┌──────────────┐ ┌──────────────────┐ ┌────────────────────┐           │ │
│  │ │ gold.baseline│ │ gold.longitudinal│ │ gold.occurrence    │           │ │
│  │ │ 组级汇总     │ │ 组级汇总         │ │ 组级汇总           │           │ │
│  │ └──────────────┘ └──────────────────┘ └────────────────────┘           │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│ Metadata Schema                                                             │
│ ┌──────────────────┐ ┌─────────────────┐ ┌──────────────────┐              │
│ │ meta.output_spec │ │ meta.derivations│ │ meta.schema_docs │              │
│ └──────────────────┘ └─────────────────┘ └──────────────────┘              │
│ ┌─────────────────────┐ ┌─────────────────┐                                │
│ │ meta.output_assembly│ │ meta.data_catalog│                                │
│ └─────────────────────┘ └─────────────────┘                                │
└─────────────────────────────────────────────────────────────────────────────┘

                                    │
                                    ▼
                         数据导出接口 (CSV/Parquet)
                                    │
                                    ▼
                    下游系统 (prism-render, prism-agent, R/Python)
```

### 1.2 核心设计理念

**Subject Level → Group Level → Export**

| Layer | 粒度 | 内容 | 用途 |
|-------|------|------|------|
| **Bronze** | As-collected | EDC原始数据 | 数据存档、审计追溯 |
| **Silver** | Subject Level | 受试者粒度的分析就绪数据 | 详细数据查询、个体分析 |
| **Gold** | Group Level | 组别汇总的统计量 | 统计表格、分析报告 |

**设计原则**:
1. **单一数据库** - 一个study的所有数据在一个DuckDB文件中
2. **元数据驱动** - Schema、衍生规则、输出定义都存在meta表中
3. **统一接口** - 三个schema提供一致的数据访问模式
4. **版本控制** - 支持衍生版本、统计版本的追溯

### 1.3 三种Schema（贯穿Bronze/Silver/Gold）

| Schema | 粒度 | 典型内容 | Bronze示例 | Silver示例 | Gold用途 |
|--------|------|----------|-----------|-----------|---------|
| **baseline** | 1 row per subject | 人口学、基线特征、治疗分配、分析集flag | bronze.demog | silver.baseline | 人口学表、基线特征表 |
| **longitudinal** | 1 row per subject × param × visit | 实验室、生命体征、疗效评分（含BASE/CHG） | bronze.labs, bronze.vs | silver.longitudinal | 访视汇总表、变化趋势图 |
| **occurrence** | 1 row per event | 不良事件、合并用药、病史、手术 | bronze.ae, bronze.cm | silver.occurrence | AE汇总表、CM列表 |

---

## 二、数据层详细设计

Gold Layer是Silver的组别汇总视图：
- **Silver**：每个受试者的详细数据
- **Gold**：按组别（treatment、subgroup等）汇总的统计量

### 2.2 Gold表结构：长表 + 多维度分组

**统一的长表结构**，支持多维度分组和假设检验：

```sql
CREATE TABLE gold.baseline (
    output_id TEXT,              -- 标识为哪个output生成的统计
    
    -- 分组维度（支持多层）
    group1_name TEXT,            -- 'TRTA'
    group1_value TEXT,           -- 'Drug A', 'Placebo', 'Total'
    group2_name TEXT,            -- 'SEX', 'AGEGROUP' (亚组，可NULL)
    group2_value TEXT,           -- 'Male', '>65' (可NULL)
    
    -- 比较维度（假设检验用）
    comparison TEXT,             -- NULL 或 'Drug A vs Placebo'
    
    -- 变量/类别
    variable TEXT,               -- 'AGE', 'SEX'
    category TEXT,               -- 分类变量的值 (可NULL)
    
    -- 统计量
    stat_name TEXT,              -- 'n', 'mean', 'sd', 'median', 'pct', 'diff', 'ci', 'p_value'
    stat_value REAL,
    stat_display TEXT,           -- 格式化显示值
    row_order INTEGER
);

CREATE TABLE gold.longitudinal (
    output_id TEXT,
    
    -- 分组维度
    group1_name TEXT,
    group1_value TEXT,
    group2_name TEXT,
    group2_value TEXT,
    
    -- 比较维度
    comparison TEXT,
    
    -- 参数/访视
    paramcd TEXT,
    visit TEXT,
    
    -- 统计量
    stat_name TEXT,              -- 'n', 'mean', 'chg', 'lsmean', 'diff', 'se', 'ci', 'p_value'
    stat_value REAL,
    stat_display TEXT,
    row_order INTEGER
);

CREATE TABLE gold.occurrence (
    output_id TEXT,
    
    -- 分组维度
    group1_name TEXT,
    group1_value TEXT,
    group2_name TEXT,
    group2_value TEXT,
    
    -- 比较维度
    comparison TEXT,
    
    -- 分类层级（支持多层如SOC→PT）
    cat1_name TEXT,              -- 'SOC', 'ATC1'
    cat1_value TEXT,             -- 'Infections'
    cat2_name TEXT,              -- 'PT', 'ATC2' (可NULL)
    cat2_value TEXT,             -- 'Pneumonia' (可NULL)
    
    -- 统计量
    stat_name TEXT,              -- 'n', 'pct', 'rate_diff', 'rr', 'p_value'
    stat_value REAL,
    stat_display TEXT,
    row_order INTEGER
);
```

### 2.3 长表设计的优势

| 场景 | 长表 | 宽表 |
|------|------|------|
| 新增统计量 | ✓ 只需加行 | ✗ 需改表结构 |
| 稀疏数据 | ✓ 不浪费空间 | ✗ 大量NULL |
| 灵活查询 | ✓ 易筛选、透视 | ✗ 结构固定 |
| 统一性 | ✓ 三schema结构一致 | ✗ 各自不同 |
| 渲染引擎 | ✓ 通用模板 | ✗ 需定制 |

### 2.4 典型场景举例

#### 场景1：简单by treatment汇总
```
output_id='T1_demog', group1_name='TRTA', group1_value='Drug A', 
group2_name=NULL, comparison=NULL,
variable='AGE', category=NULL, stat_name='mean', stat_value=45.2
```

#### 场景2：亚组分析 (by treatment + sex)
```
output_id='T2_subgrp', group1_name='TRTA', group1_value='Drug A',
group2_name='SEX', group2_value='Male',
variable='AGE', stat_name='mean', stat_value=47.1
```

#### 场景3：假设检验 (Drug A vs Placebo)
```
output_id='T1_demog', group1_name='TRTA', group1_value=NULL,
comparison='Drug A vs Placebo',
variable='AGE', stat_name='diff', stat_value=2.1
+ stat_name='p_value', stat_value=0.043
```

#### 场景4：SOC→PT双层分类
```
output_id='T4_teae', group1_name='TRTA', group1_value='Drug A',
cat1_name='SOC', cat1_value='Infections',
cat2_name='PT', cat2_value='Pneumonia',
stat_name='n', stat_value=5
```

### 2.5 Flag筛选的处理

通过 **output_id** 区分不同筛选条件的统计：
- `output_id='T_TEAE'` — 所有治疗期AE
- `output_id='T_SAE'` — 严重AE（AESER='Y'）
- `output_id='T_RELDAE'` — 相关AE（AEREL='Y'）
- `output_id='T_CM_CON'` — 伴随用药
- `output_id='T_CM_PRIOR'` — 既往用药

筛选条件在 `meta.output_spec` 定义，Gold只存结果。

### 2.6 Gold为何用物化表而非View

| 方面 | 物化表 | View |
|------|--------|------|
| 复杂统计 | ✓ 可存储MMRM/Cox等R/Python结果 | ✗ SQL无法计算 |
| 性能 | ✓ 预计算，查询快 | ✗ 每次实时计算 |
| 版本控制 | ✓ 可追溯历史版本 | ✗ 动态生成 |
| 一致性 | ✓ "一个数据库=整个study" | △ 依赖Silver |

**结论**：Gold用物化表，支持将复杂统计模型的结果也存回数据库。

---

## 三、Metadata 详细设计

### 3.0 设计原则

```
参考库 (可外链/跨study共享)        Study-specific
├── meta.params                    ├── meta.study_info
├── meta.flags                     ├── meta.variables
└── meta.visits                    ├── meta.derivations
                                   ├── meta.outputs
                                   └── ...
```

- **每个study一个独立的db文件**
- **参考库（params/flags/visits）可以从外部库导入或本地定义**
- **跨study共享在spec文件层面**，import时各自导入

### 3.1 meta.study_info (Study基本信息)

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

### 3.2 meta.params (参数库 - 可外链)

定义longitudinal schema的参数，支持跨study复用：

```sql
CREATE TABLE meta.params (
    param_id TEXT PRIMARY KEY,           -- 'param_phga'
    paramcd TEXT NOT NULL UNIQUE,        -- 'PHGA'
    param_label TEXT NOT NULL,           -- 'Physician Global Activity'
    param_desc TEXT,
    
    -- 参数特性
    category TEXT,                       -- 'efficacy', 'safety', 'pk', 'pd'
    data_type TEXT,                      -- 'continuous', 'categorical', 'ordinal'
    unit TEXT,                           -- 'cm', 'points', 'U/L'
    
    -- 来源信息 (默认值)
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

### 3.3 meta.flags (Flag库 - 可外链)

定义occurrence schema的事件标志：

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

### 3.4 meta.visits (Analysis Visit库)

定义分析用Visit：

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

### 3.5 meta.variables (变量表)

统一的变量注册表：

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
```

### 3.6 meta.derivations (衍生规则)

Agent用这个表了解如何衍生变量/参数：

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

### 3.7 meta.outputs (输出定义)

```sql
CREATE TABLE meta.outputs (
    output_id TEXT PRIMARY KEY,          -- 'T1_demog', 'F1_phga'
    output_type TEXT NOT NULL,           -- 'table', 'listing', 'figure'
    title TEXT,
    
    schema TEXT NOT NULL,                -- 'baseline', 'longitudinal', 'occurrence'
    source_block TEXT,
    
    -- Analysis settings
    population TEXT,                     -- 'SAFFL', 'FASFL'
    visit_filter TEXT,                   -- list of visits
    filter_expr TEXT,
    
    -- Rendering
    render_function TEXT,
    render_options TEXT,                 -- JSON
    
    section TEXT,
    display_order INTEGER,
    
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 3.8 meta.output_variables (输出-变量关联)

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

### 3.9 meta.output_params (输出-参数关联)

```sql
CREATE TABLE meta.output_params (
    id INTEGER PRIMARY KEY,
    output_id TEXT NOT NULL,
    paramcd TEXT NOT NULL,               -- FK → meta.params
    
    display_order INTEGER,
    
    UNIQUE(output_id, paramcd)
);
```

### 3.10 meta.functions (函数库)

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

### 3.11 meta.dependencies (依赖关系)

```sql
CREATE TABLE meta.dependencies (
    id INTEGER PRIMARY KEY,
    from_var TEXT NOT NULL,
    to_var TEXT NOT NULL,
    
    UNIQUE(from_var, to_var)
);
```

### 3.12 Meta Schema ER图

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

## 四、完整工作流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 1: Parse ALS → Bronze + meta.schema_docs                              │
│  【确定性脚本】解析ALS文件，创建Bronze表，记录schema文档                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 2: 定义 output_spec（手动/协作）                                       │
│  • 定义每个output需要什么变量/参数                                           │
│  • 定义分组方式、统计方法、筛选条件                                           │
│  • 可通过Excel导入或AI辅助生成                                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 3: 分析依赖 → 识别需要衍生的变量                                       │
│  【Agent】对比output_spec的required_vars与data_catalog，找出缺失变量          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 4: 定义 derivations（协作）                                            │
│  • 简单衍生：直接写SQL                                                       │
│  • 复杂衍生：外链rule_docs/*.md，AI生成SQL                                   │
│  • 记录依赖关系                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 5: 执行衍生 → Silver Layer                                            │
│  【执行引擎】按依赖顺序执行SQL，生成Silver表，更新schema_docs                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 6: 计算统计 → Gold Layer                                              │
│  【分析引擎】                                                                 │
│  • 简单统计：SQL直接计算（描述统计、t检验、卡方）                            │
│  • 复杂统计：调用R/Python（MMRM、Cox、生存分析），结果写回Gold              │
│  • 生成长表形式的统计量                                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 7: 渲染 → Platinum Layer                                              │
│  【渲染引擎】                                                                 │
│  • 根据output_assembly从Gold查询数据                                         │
│  • 应用layout模板                                                            │
│  • 使用python-pptx/r2rtf/weasyprint生成PPT/RTF/PDF                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 关键设计点

1. **Output-Driven**：从最终要什么倒推需要什么数据
2. **Agent边界清晰**：只能访问meta表，不能访问实际数据
3. **分层执行**：简单SQL vs 复杂R/Python，结果统一存回Gold
4. **物化表**：Gold用物化表支持复杂统计结果持久化
5. **长表结构**：Gold统一用长表，灵活支持任意统计量组合

---

## 五、为什么选择DuckDB

| 特性 | DuckDB | SQLite |
|------|--------|--------|
| **分析性能** | 列存储，分析查询快10-100x | 行存储，OLTP优化 |
| **R集成** | 原生支持Arrow，零拷贝传输 | 需要转换 |
| **Python集成** | pandas/polars无缝集成 | 需要转换 |
| **窗口函数** | 完整支持 | 基本支持 |
| **并发写入** | 单写多读 | 单写多读 |
| **行业趋势** | 数据工程新标准 | 传统嵌入式数据库 |

**DuckDB更适合分析场景**，尤其是临床数据这种需要大量聚合、窗口函数的场景。

---

## 六、Agent交互边界

### Agent可访问的信息（通过meta表）：
- `meta.schema_docs` - 每层每表每列的结构说明
- `meta.data_catalog` - 变量目录
- `meta.output_spec` - 输出需求
- `meta.output_assembly` - 组装规则
- `meta.derivations` - 现有衍生规则

### Agent不能直接访问的：
- 实际数据（bronze/silver/gold表的数据行）

### Agent的任务：
1. 根据output_spec分析需要哪些衍生
2. 根据schema_docs理解数据结构
3. 生成衍生SQL代码
4. 生成统计SQL或R/Python代码
5. 读取rule_docs理解复杂逻辑

---

## 七、项目文件结构

```
📁 prism-agent/
├── src/prism/                    # 核心代码库
│   ├── __init__.py
│   ├── parse_als.py              # ALS解析器
│   ├── init_bronze.py            # Bronze层初始化
│   ├── derive_silver.py          # Silver层衍生执行
│   ├── compute_gold.py           # Gold层统计计算
│   ├── render_platinum.py        # Platinum层渲染
│   └── schema_documenter.py      # Schema文档生成
│
├── docs/                         # 项目文档
│   ├── ARCHITECTURE.md           # 本架构设计文档
│   ├── API.md                    # API文档
│   └── references/               # 参考资料
│
├── rule_docs/                    # 复杂衍生规则文档
│   ├── mmt8.md                   # MMT8评分计算规则
│   ├── haqdi.md                  # HAQ-DI评分规则
│   └── ...
│
├── examples/                     # 示例研究
│   └── D8318N00001/
│       ├── D8318N00001_ALS.xlsx  # EDC Schema (ALS文件)
│       ├── study.duckdb          # DuckDB数据库
│       ├── output_spec.xlsx      # 输出定义（手动维护）
│       └── outputs/              # 生成的Platinum层文件
│           ├── slide_deck.pptx
│           ├── tables.rtf
│           └── figures.pdf
│
├── ARCHITECTURE.md               # 本文档
├── PROJECT_PLAN.md               # 项目实施计划
└── README.md                     # 项目说明
```

---

## 附录：术语对照

| 旧术语 | 新术语 v3.0 | 说明 |
|--------|-------------|------|
| Raw Layer | Bronze Layer | Medallion架构标准 |
| Derived Layer | Silver Layer | Medallion架构标准 |
| Output Layer | Gold Layer | Medallion架构标准 |
| - | Platinum Layer | 新增：渲染输出层 |
| snapshot | static | 已弃用 |
| static | **baseline** | v3.0更新：避免混淆 |
| measurement | longitudinal | 纵向数据 |
| event | occurrence | CDISC术语 |
| data_dictionary | data_catalog | 数据工程标准 |
| output_manifest | output_spec | 输出定义 |
| transformation_rules | derivations | 衍生规则 |

---

**文档版本历史**：
- v1.0 (2026-01-XX): 初始设计 - 三层架构
- v2.0 (2026-02-10): 重构 - Medallion架构
- v3.0 (2026-02-12): 最终设计 - Gold Layer长表设计，Platinum层明确化
