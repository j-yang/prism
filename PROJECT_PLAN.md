# PRISM - 项目实施计划

**更新日期**: 2026-02-12  
**状态**: Phase 1 完成, Phase 2 进行中

---

## 项目概述

**项目名称**: PRISM (Pooled Research Intelligence & Statistical Mapping)  
**目标**: 构建一个数据库驱动的临床数据自动化处理框架，支持跨study的标准化分析和输出生成  
**技术栈**: DuckDB + Python + R + python-pptx/r2rtf  
**核心理念**: Agent生成代码，用户执行  

### Agent = Code Generator (不是Executor)

```
Agent读取: ALS, Spec, Meta, Rule Docs
    ↓
Agent输出: SQL/R/Python 脚本
    ↓
用户执行脚本 → 数据处理 → 输出
```

**Agent绝不接触真实患者数据**

详细架构设计见 [ARCHITECTURE.md](ARCHITECTURE.md)

---

## 架构概览

```
Bronze (Raw) → Silver (Subject Level) → Gold (Group Level) → Platinum (Deliverables)
     │                  │                      │                      │
  EDC数据          分析就绪数据            统计汇总              PPT/RTF/PDF
```

**三种Schema（贯穿所有层）**:
- **baseline**: 1 row per subject (人口学、基线)
- **longitudinal**: 1 row per subject × param × visit (实验室、疗效)
- **occurrence**: 1 row per event (AE、CM、MH)

详细架构设计见 [ARCHITECTURE.md](ARCHITECTURE.md)

---

## 项目实施阶段

### Phase 1: 数据库框架 ✅ 已完成

**目标**: 建立Bronze层基础架构

#### 1.1 迁移到DuckDB ✅
- [x] 安装DuckDB Python包
- [x] 创建数据库初始化脚本
- [x] 实现database.py连接管理
- [x] 测试基本CRUD操作

#### 1.2 基础Metadata表 ✅
- [x] 创建 `meta.schema_docs` 表
- [x] 创建 `meta.data_catalog` 表
- [x] 实现metadata.py CRUD接口

#### 1.3 ALS解析器 ✅
- [x] 基本ALS解析功能
- [x] Form分类功能 (baseline/longitudinal/occurrence)
- [x] 自动生成Bronze层DDL
- [x] 自动填充 `meta.schema_docs`
- [x] 自动填充 `meta.data_catalog`

#### 1.4 Bronze层初始化 ✅
- [x] 实现 `init_bronze.py`
- [x] SAS/CSV数据导入接口
- [x] SAS日期转换 (1960 epoch)
- [x] 数据验证规则
- [x] 单元测试 (test_phase1_4.py)

**Phase 1 交付物** ✅:
- `src/prismdb/database.py` - 数据库连接管理
- `src/prismdb/metadata.py` - 元数据CRUD
- `src/prismdb/parse_als_v2.py` - ALS解析器
- `src/prismdb/classify_forms_v2.py` - Form分类
- `src/prismdb/init_bronze.py` - Bronze数据导入
- `sql/init_metadata.sql` - 基础Meta DDL
- 测试数据集（D8318N00001）
- Phase1_Complete.md 文档

---

### Phase 2: Meta Schema & Silver层框架 🔄 进行中

**目标**: 设计完整的Meta Schema，实现Bronze → Silver转换

#### 2.0 Meta Schema设计 ✅
- [x] 设计11张Meta表结构
- [x] 参考库设计 (params/flags/visits - 可外链)
- [x] 变量统一注册表 (meta.variables)
- [x] 衍生规则表 (meta.derivations)
- [x] 输出定义表 (meta.outputs)
- [x] 设计文档: docs/META_SCHEMA.md
- [x] 双层设计: DDL + Python Models

**双层Schema设计**:

| Layer | 位置 | 用途 |
|-------|------|------|
| DDL | `sql/init_meta.sql` | 数据库表定义 |
| Python Models | `src/prismdb/schema/models.py` | Agent解析/验证/代码生成 |

**11张Meta表 + Python Model对应**:

| 类别 | 表名 | Python Model | 用途 |
|------|------|--------------|------|
| 参考库 | `meta.params` | `Parameter` | 参数库 (可外链) |
| 参考库 | `meta.flags` | `Flag` | Flag库 (可外链) |
| 参考库 | `meta.visits` | `Visit` | Visit库 (可外链) |
| Study | `meta.study_info` | `StudyInfo` | 当前study信息 |
| Study | `meta.variables` | `Variable` | 变量注册表 |
| Study | `meta.derivations` | `Derivation` | 衍生规则 |
| Study | `meta.outputs` | `Output` | 输出定义 |
| Study | `meta.output_variables` | `OutputVariable` | 输出-变量关联 |
| Study | `meta.output_params` | `OutputParam` | 输出-参数关联 |
| Study | `meta.functions` | `Function` | 复杂函数库 |
| Study | `meta.dependencies` | `Dependency` | 依赖关系 |

#### 2.1 Meta Schema实现
- [ ] 创建 `sql/init_meta.sql` (DDL)
- [ ] 创建 `src/prismdb/schema/models.py` (Python Models)
- [ ] 更新 `src/prismdb/metadata.py` 支持新表
- [ ] 创建参考库导入工具

#### 2.2 Spec Parser
- [ ] 创建 `src/prismdb/import_spec.py`
- [ ] 解析centralized_mapping_spec.xlsx
- [ ] 导入到Meta表
- [ ] 支持外链参数库/Flag库

#### 2.3 衍生代码生成 (Agent Core)
- [ ] 实现依赖分析 (拓扑排序)
- [ ] 生成SQL衍生代码 (不是执行)
- [ ] 支持复杂衍生 (rule_docs外链)
- [ ] 生成Bronze → Silver转换脚本

**Phase 2 交付物**:
- 完整的Meta Schema DDL
- Python Models (Pydantic)
- Spec Parser工具
- 衍生代码生成器 (not executor)
- Silver层生成脚本模板

---

### Phase 3: Gold层统计框架

**目标**: 实现Silver → Gold的统计计算

#### 3.1 设计output_spec规范
- [ ] 定义output_spec Excel格式
- [ ] output_spec导入脚本
- [ ] output_spec验证规则
- [ ] 示例output_spec（demographics, labs, AE）

**预计工作量**: 2-3天

#### 3.2 实现简单统计计算
- [ ] 实现 `compute_gold.py`
- [ ] 描述统计（n, mean, sd, median, min, max）
- [ ] 分类统计（n, pct）
- [ ] t检验/ANOVA
- [ ] 卡方检验/Fisher精确检验
- [ ] 生成长表结构的Gold数据

**预计工作量**: 4-5天

#### 3.3 实现复杂统计接口
- [ ] R接口（通过rpy2或subprocess）
- [ ] Python统计库接口（statsmodels, lifelines）
- [ ] MMRM示例（R mmrm包）
- [ ] Cox回归示例（Python lifelines）
- [ ] 结果写回Gold表

**预计工作量**: 4-5天

#### 3.4 支持多维度分组和假设检验
- [ ] 多维度分组实现（group1 + group2）
- [ ] 分层统计（如分层t检验）
- [ ] 两两比较（pairwise）
- [ ] vs control比较
- [ ] 亚组分析框架

**预计工作量**: 3-4天

**Phase 3 交付物**:
- output_spec定义规范
- compute_gold统计引擎
- 简单统计库（SQL）
- 复杂统计接口（R/Python）
- Gold层完整生成流程
- Phase 3文档

---

### Phase 4: Platinum层渲染引擎

**目标**: 实现Gold → Platinum的输出渲染

#### 4.1 设计output_assembly规范
- [ ] 定义assembly规则格式
- [ ] 定义layout模板类型
- [ ] 定义formatting规则
- [ ] 示例assembly定义

**预计工作量**: 2-3天

#### 4.2 实现PPT渲染器
- [ ] 实现 `render_platinum.py`
- [ ] python-pptx集成
- [ ] Table渲染器
- [ ] Figure渲染器（matplotlib/ggplot）
- [ ] Listing渲染器
- [ ] 模板系统（title, footnote, layout）

**预计工作量**: 5-6天

#### 4.3 实现RTF渲染器
- [ ] r2rtf集成（通过R）
- [ ] 或 python-docx作为备选
- [ ] Table格式化（FDA风格）
- [ ] Listing格式化
- [ ] 页眉页脚

**预计工作量**: 3-4天

#### 4.4 通用Layout模板
- [ ] by_variable模板（demographics）
- [ ] by_visit模板（longitudinal）
- [ ] by_category模板（AE/CM）
- [ ] 自定义模板引擎
- [ ] 模板库

**预计工作量**: 3-4天

#### 4.5 端到端验证
- [ ] 完整流程测试（ALS → PPT）
- [ ] 多study测试
- [ ] 性能测试
- [ ] 输出质量验证

**预计工作量**: 3-4天

**Phase 4 交付物**:
- output_assembly规范
- render_platinum渲染引擎
- PPT/RTF渲染器
- Layout模板库
- 端到端测试报告
- Phase 4文档

---

### Phase 5: Agent = Code Generator

**目标**: 实现AI Agent作为代码生成器，不是执行器

**核心原则**:
- Agent读取: ALS, Spec, Meta Schema, Rule Docs
- Agent输出: SQL/R/Python脚本
- 用户执行生成的代码
- Agent **绝不**接触真实患者数据

#### 5.1 Agent架构设计
- [ ] 定义Agent输入接口 (读取meta表)
- [ ] 定义Agent输出格式 (生成脚本)
- [ ] CLI设计 (`prism generate bronze/silver/gold`)
- [ ] 用户工作流设计

**用户工作流**:
```bash
# 1. 初始化项目
prism init --als D8318N00001_ALS.xlsx --spec mapping_spec.xlsx

# 2. Agent生成Bronze代码
prism generate bronze
# → 生成 scripts/01_init_bronze.py

# 3. 你review并执行
python scripts/01_init_bronze.py

# 4. Agent生成Silver代码
prism generate silver
# → 生成 scripts/02_derive_silver.sql

# 5. 你review并执行
duckdb study.duckdb < scripts/02_derive_silver.sql
```

#### 5.2 Bronze代码生成
- [ ] 解析ALS → 生成Bronze DDL
- [ ] 生成数据导入脚本
- [ ] SAS/CSV读取代码模板

#### 5.3 Silver代码生成
- [ ] 读取meta.derivations
- [ ] 依赖分析 (拓扑排序)
- [ ] 生成衍生SQL脚本
- [ ] 利用rule_docs理解复杂逻辑

#### 5.4 Gold代码生成
- [ ] 读取meta.outputs
- [ ] 生成统计SQL
- [ ] 复杂统计：生成R/Python代码
- [ ] 代码模板库

#### 5.5 Platinum代码生成
- [ ] 生成渲染R脚本
- [ ] 生成autoslider spec YAML
- [ ] 生成python-pptx脚本

**Phase 5 交付物**:
- `prism` CLI工具
- 代码生成器 (不是执行器)
- 代码模板库
- 生成脚本示例
- 用户文档

---

## 时间线估算

| Phase | 任务 | 预计工作量 | 状态 |
|-------|------|-----------|------|
| Phase 1 | 数据库框架 | 10-14天 | 🟡 进行中 |
| Phase 2 | Silver层衍生 | 13-17天 | ⚪ 未开始 |
| Phase 3 | Gold层统计 | 13-17天 | ⚪ 未开始 |
| Phase 4 | Platinum渲染 | 16-21天 | ⚪ 未开始 |
| Phase 5 | Agent集成 | 13-16天 | ⚪ 未开始 |
| **总计** | | **65-85天** | |

*注：工作量为实际开发时间，不包括学习、调研、会议等*

---

## 当前进度

### ✅ 已完成
- [x] 架构设计最终确认（v3.0）
- [x] 四层架构定义
- [x] Gold Layer长表设计
- [x] Metadata表结构设计
- [x] 术语标准化（baseline/longitudinal/occurrence）
- [x] ALS解析基础功能
- [x] Form分类功能

### 🚧 进行中
- [ ] DuckDB迁移
- [ ] Metadata表实现

### 📋 待办
- Phase 1剩余任务
- Phase 2-5全部任务

---

## 风险与挑战

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 复杂统计模型集成 | 高 | 早期原型验证，准备R/Python备选方案 |
| 跨study差异处理 | 中 | study_overrides机制，充分测试 |
| Agent代码质量 | 中 | Human-in-the-loop，代码review机制 |
| 性能问题（大数据） | 中 | DuckDB优化，索引设计，分批处理 |
| 渲染格式复杂性 | 低 | 从简单模板开始，逐步扩展 |

---

## 成功标准

### Phase 1
- [ ] 能够从ALS文件自动生成Bronze层
- [ ] meta表完整且可查询
- [ ] 通过单元测试（覆盖率>80%）

### Phase 2
- [ ] 能够从Bronze自动生成Silver层
- [ ] 支持至少10个常见衍生变量
- [ ] 支持1个复杂衍生示例（如MMT8）

### Phase 3
- [ ] 能够从Silver自动生成Gold层
- [ ] 支持描述统计、t检验、卡方
- [ ] 支持1个复杂统计示例（如MMRM）

### Phase 4
- [ ] 能够从Gold自动生成PPT
- [ ] 支持至少3种output类型（table/figure/listing）
- [ ] 输出符合FDA格式要求

### Phase 5
- [ ] Agent能够自动生成80%+的衍生SQL
- [ ] Agent生成的代码正确率>90%
- [ ] 完整端到端流程<5分钟（小型study）

---

## 项目文件结构

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
│   ├── ARCHITECTURE.md           # 架构设计文档
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
├── ARCHITECTURE.md               # 架构设计文档
├── PROJECT_PLAN.md               # 本文档
├── README.md                     # 项目说明
└── requirements.txt
```

---

## 下一步行动

### 立即开始（本周）
1. [ ] 安装配置DuckDB
2. [ ] 创建数据库初始化脚本
3. [ ] 迁移ALS解析器到DuckDB
4. [ ] 实现meta.schema_docs基础功能

### 近期计划（2周内）
1. [ ] 完成Phase 1全部任务
2. [ ] 准备Phase 2设计文档
3. [ ] 搭建测试框架

### 中期目标（1月内）
1. [ ] 完成Phase 1-2
2. [ ] 开始Phase 3
3. [ ] 完善文档和测试

---

## 术语对照表

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
| spec_file | rule_doc | 复杂衍生规则文档 |
| ALS | EDC Schema | 数据库结构定义文件 |

---

**文档版本**: v2.0  
**最后更新**: 2026-02-12

### 1.1 数据库Schema设计与创建

**目标**：创建SQLite数据库结构

**任务清单**：
- [ ] 1.1.1 设计完整的数据库schema
  - [ ] 定义所有表的字段、类型、约束
  - [ ] 定义主键、外键关系
  - [ ] 定义索引策略
- [ ] 1.1.2 编写建表SQL脚本
  - [ ] `create_schema.sql`
- [ ] 1.1.3 创建示例数据库
  - [ ] `study_template.db`

**交付物**：
```
📁 database/
├── create_schema.sql      # 建表脚本
├── study_template.db      # 空数据库模板
└── schema_documentation.md # Schema说明文档
```

**Schema详细设计**：

```sql
-- ============================================
-- Metadata Tables (Catalog)
-- ============================================

-- 研究列表
CREATE TABLE studies (
    study_code TEXT PRIMARY KEY,
    study_name TEXT,
    indication TEXT NOT NULL,
    phase TEXT,
    status TEXT DEFAULT 'active',
    edc_schema_file TEXT,  -- ALS file path
    raw_data_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 变量目录 Data Catalog（从EDC Schema/ALS生成）
CREATE TABLE data_catalog (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    study_code TEXT REFERENCES studies(study_code),
    var_name TEXT NOT NULL,
    structure TEXT NOT NULL CHECK (structure IN ('static', 'longitudinal', 'occurrence')),
    label TEXT,
    data_type TEXT,
    length INTEGER,
    source_form TEXT,
    source_field TEXT,
    codelist TEXT,  -- JSON格式
    is_derived BOOLEAN DEFAULT FALSE,
    UNIQUE(study_code, var_name, structure)
);

-- 转换规则 Transformation Rules
CREATE TABLE transformation_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    var_name TEXT NOT NULL,
    structure TEXT NOT NULL CHECK (structure IN ('static', 'longitudinal', 'occurrence')),
    study_code TEXT,  -- NULL表示全局规则
    depends_on TEXT,  -- 逗号分隔的依赖变量
    transformation_sql TEXT NOT NULL,
    description TEXT,
    complexity TEXT CHECK (complexity IN ('simple', 'medium', 'complex')),
    rule_doc TEXT,  -- 复杂转换的外链Rule Document (md)
    execution_order INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (study_code) REFERENCES studies(study_code)
);

-- 参数知识库 Parameter Catalog
CREATE TABLE parameter_catalog (
    paramcd TEXT PRIMARY KEY,
    param TEXT NOT NULL,
    category TEXT CHECK (category IN ('lab', 'efficacy', 'vital', 'biomarker', 'other')),
    unit TEXT,
    indication TEXT,  -- 逗号分隔，如 'IIM,SSC' 或 'COMMON'
    derivation_type TEXT CHECK (derivation_type IN ('direct', 'composite', 'complex')),
    source_form TEXT,
    transformation_sql TEXT,
    rule_doc TEXT,
    loinc_code TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 输出清单 Output Manifest
CREATE TABLE output_manifest (
    output_id TEXT PRIMARY KEY,
    output_type TEXT NOT NULL CHECK (output_type IN ('table', 'figure', 'listing')),
    source_structure TEXT NOT NULL CHECK (source_structure IN ('static', 'longitudinal', 'occurrence')),
    columns TEXT NOT NULL,  -- 逗号分隔
    filter_expr TEXT,
    param_filter TEXT,  -- longitudinal用，逗号分隔的PARAMCD
    group_by TEXT,
    autoslider_func TEXT,
    title_template TEXT,
    footnote_template TEXT,
    sort_order INTEGER,
    is_active BOOLEAN DEFAULT TRUE
);

-- 输出-研究关联（支持study级别的覆盖）
CREATE TABLE output_study_config (
    output_id TEXT REFERENCES output_manifest(output_id),
    study_code TEXT REFERENCES studies(study_code),
    is_applicable BOOLEAN DEFAULT TRUE,
    override_columns TEXT,
    override_filter TEXT,
    override_params TEXT,
    notes TEXT,
    PRIMARY KEY (output_id, study_code)
);

-- ============================================
-- Raw Layer (Bronze) - 从EDC导入
-- ============================================

-- Raw Static（截面数据，一人一条）
CREATE TABLE raw_static (
    usubjid TEXT PRIMARY KEY,
    study_code TEXT REFERENCES studies(study_code),
    -- 以下字段根据实际EDC Schema动态添加
    -- age, sex, race, etc.
    import_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Raw Longitudinal（纵向数据，一人×参数×时点）
CREATE TABLE raw_longitudinal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usubjid TEXT NOT NULL,
    study_code TEXT REFERENCES studies(study_code),
    paramcd TEXT NOT NULL,
    param TEXT,
    visit TEXT,
    visitnum INTEGER,
    adt TEXT,  -- Analysis date
    aval REAL,
    avalc TEXT,
    domain TEXT,  -- 来源domain标识
    ablfl TEXT,  -- Baseline flag
    import_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(usubjid, paramcd, visit, domain)
);

-- Raw Occurrence（事件数据，一事件一条）
CREATE TABLE raw_occurrence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usubjid TEXT NOT NULL,
    study_code TEXT REFERENCES studies(study_code),
    domain TEXT NOT NULL,  -- AE, CM, EC, etc.
    seq INTEGER,
    term TEXT,
    decod TEXT,
    cat TEXT,  -- Category
    scat TEXT, -- Subcategory
    astdt TEXT,  -- Start date
    aendt TEXT,  -- End date
    -- 其他字段根据domain类型添加
    import_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(usubjid, domain, seq)
);

-- ============================================
-- Derived Layer (Silver) - 转换结果
-- ============================================

-- Derived Static（raw + 衍生变量）
CREATE TABLE derived_static (
    usubjid TEXT PRIMARY KEY,
    study_code TEXT,
    -- Raw fields copied from raw_static
    -- Derived fields: trtsdt, trtedt, trtdur, saffl, bl_xxx, etc.
    derivation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Derived Longitudinal（raw + 衍生字段）
CREATE TABLE derived_longitudinal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usubjid TEXT NOT NULL,
    study_code TEXT,
    paramcd TEXT NOT NULL,
    param TEXT,
    visit TEXT,
    visitnum INTEGER,
    adt TEXT,
    aval REAL,
    avalc TEXT,
    base REAL,  -- Baseline value
    chg REAL,   -- Change from baseline
    pchg REAL,  -- Percent change
    ablfl TEXT,
    anl01fl TEXT,  -- Analysis flag
    derivation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(usubjid, paramcd, visit)
);

-- Derived Occurrence（raw + flags）
CREATE TABLE derived_occurrence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usubjid TEXT NOT NULL,
    study_code TEXT,
    domain TEXT NOT NULL,
    seq INTEGER,
    term TEXT,
    decod TEXT,
    astdt TEXT,
    aendt TEXT,
    -- Flags
    teaefl TEXT,
    saefl TEXT,
    relfl TEXT,
    serfl TEXT,
    dthfl TEXT,
    -- 其他flag根据需要添加
    derivation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(usubjid, domain, seq)
);

-- ============================================
-- Output Layer (Gold) - 输出视图（示例）
-- ============================================

-- 人口学输出视图
CREATE VIEW output_demog AS
SELECT 
    s.usubjid, s.study_code, s.age, s.sex, s.race,
    d.trtsdt, d.saffl, d.trta
FROM raw_static s
JOIN derived_static d ON s.usubjid = d.usubjid
WHERE d.saffl = 'Y';

-- ============================================
-- Indexes
-- ============================================

CREATE INDEX idx_longitudinal_usubjid ON raw_longitudinal(usubjid);
CREATE INDEX idx_longitudinal_paramcd ON raw_longitudinal(paramcd);
CREATE INDEX idx_longitudinal_visit ON raw_longitudinal(visit);
CREATE INDEX idx_occurrence_usubjid ON raw_occurrence(usubjid);
CREATE INDEX idx_occurrence_domain ON raw_occurrence(domain);
CREATE INDEX idx_derived_long_usubjid ON derived_longitudinal(usubjid);
CREATE INDEX idx_derived_long_paramcd ON derived_longitudinal(paramcd);
```

---

### 1.2 Excel Spec模板设计

**目标**：创建用户友好的Excel编辑模板

**任务清单**：
- [ ] 1.2.1 设计Excel模板结构
  - [ ] Sheet: studies
  - [ ] Sheet: transformation_rules
  - [ ] Sheet: parameter_catalog
  - [ ] Sheet: output_manifest
  - [ ] Sheet: output_study_config
- [ ] 1.2.2 添加数据验证规则
  - [ ] 下拉列表（structure, complexity, output_type等）
  - [ ] 条件格式（必填项高亮）
- [ ] 1.2.3 创建填写说明
  - [ ] 每个sheet的说明行
  - [ ] 示例数据

**交付物**：
```
📁 templates/
├── spec_template.xlsx     # Excel模板
└── spec_guide.md          # 填写指南
```

---

### 1.3 Excel到SQLite导入脚本

**目标**：实现Excel spec到数据库的自动导入

**任务清单**：
- [ ] 1.3.1 开发核心导入模块
  ```python
  # import_spec.py
  def import_studies(excel_path, db_path)
  def import_transformation_rules(excel_path, db_path)
  def import_parameter_catalog(excel_path, db_path)
  def import_output_manifest(excel_path, db_path)
  ```
- [ ] 1.3.2 数据验证逻辑
  - [ ] 必填字段检查
  - [ ] 外键引用检查
  - [ ] 数据类型验证
- [ ] 1.3.3 增量更新支持
  - [ ] 检测变更
  - [ ] 冲突处理策略
- [ ] 1.3.4 命令行接口
  ```bash
  python import_spec.py --excel spec.xlsx --db study.db
  ```

**交付物**：
```
📁 scripts/
├── import_spec.py         # 导入脚本
├── validate_spec.py       # 验证脚本
└── export_spec.py         # 导出脚本（可选，DB→Excel）
```

---

### 1.4 EDC Schema (ALS) 解析器

**目标**：从ALS文件自动生成data_catalog（确定性脚本，无需Agent）

**任务清单**：
- [ ] 1.4.1 解析ALS文件结构
  - [ ] 读取Forms sheet
  - [ ] 读取Fields sheet
  - [ ] 读取Matrices sheet
  - [ ] 读取DataDictionaries sheet
- [ ] 1.4.2 自动分类数据结构
  ```python
  def classify_form(form_oid, matrices_df) -> str:
      """返回 'static' | 'longitudinal' | 'occurrence'"""
      # 基于Addable和visit出现次数判断
  ```
- [ ] 1.4.3 生成data_catalog
  - [ ] 变量名映射（ALS field → analysis var）
  - [ ] 数据类型转换
  - [ ] Codelist提取
- [ ] 1.4.4 生成人工审核报告
  - [ ] 分类汇总
  - [ ] 待确认项标记

**交付物**：
```
📁 scripts/
├── parse_edc_schema.py    # EDC Schema (ALS) 解析器
├── generate_data_catalog.py # 生成data_catalog
└── classification_report.py # 分类审核报告
```

**分类逻辑**（确定性规则）：

```python
# parse_edc_schema.py 核心逻辑

def classify_form_structure(form_oid: str, matrices_df: pd.DataFrame, 
                            matrix_details: dict) -> str:
    """
    根据Matrix信息判断Form的数据结构类型
    
    规则（确定性，无需AI判断）：
    1. Addable=True → occurrence（可重复添加，如AE/CM/EC）
    2. 出现在多个visit → longitudinal（纵向数据）
    3. 只在一个visit出现 → static（截面数据）
    """
    # 检查是否可重复添加
    for matrix_name, matrix_df in matrix_details.items():
        if form_oid in matrix_df['FormOID'].values:
            matrix_info = matrices_df[matrices_df['OID'] == matrix_name.split('#')[1]]
            if matrix_info['Addable'].iloc[0] == True:
                return 'occurrence'
    
    # 统计出现在多少个visit
    visit_count = 0
    for matrix_name, matrix_df in matrix_details.items():
        form_row = matrix_df[matrix_df['FormOID'] == form_oid]
        if not form_row.empty:
            # 计算该form在多少个visit列有标记
            visit_cols = [c for c in matrix_df.columns if c not in ['FormOID', 'Matrix']]
            marked_visits = form_row[visit_cols].notna().sum(axis=1).iloc[0]
            visit_count = max(visit_count, marked_visits)
    
    if visit_count > 1:
        return 'longitudinal'
    else:
        return 'static'
```

---

## Phase 2: 单Study验证 (D8318N00001)

### 2.1 解析EDC Schema并生成Data Catalog

**任务清单**：
- [ ] 2.1.1 解析D8318N00001的ALS文件
- [ ] 2.1.2 生成data_catalog表
- [ ] 2.1.3 人工审核分类结果
  - [ ] 确认static/longitudinal/occurrence分类
  - [ ] 修正变量名映射
- [ ] 2.1.4 导入到数据库

---

### 2.2 导入Raw数据到Raw Layer (Bronze)

**任务清单**：
- [ ] 2.2.1 开发Raw数据导入脚本（确定性ETL）
  ```python
  def import_raw_to_bronze(raw_path, db_path, study_code):
      """将raw数据导入到raw_static/raw_longitudinal/raw_occurrence"""
  ```
- [ ] 2.2.2 处理D8318N00001的raw数据
  - [ ] 识别数据文件格式（SAS/CSV/Excel）
  - [ ] 按data_catalog映射导入
- [ ] 2.2.3 数据质量检查
  - [ ] 主键唯一性
  - [ ] 必填字段完整性

**交付物**：
```
📁 scripts/
└── import_raw.py          # Raw数据导入脚本（确定性ETL）
```

---

### 2.3 填写Spec

**任务清单**：
- [ ] 2.3.1 填写transformation_rules
  - [ ] Static衍生变量（TRTSDT, SAFFL, BL_xxx等）
  - [ ] Longitudinal衍生（BASE, CHG）
  - [ ] Occurrence flags（TEAEFL, SAEFL）
- [ ] 2.3.2 填写parameter_catalog
  - [ ] IIM/SSC的疗效参数
  - [ ] 实验室参数
- [ ] 2.3.3 填写output_manifest
  - [ ] 参考TLF shell定义输出
- [ ] 2.3.4 导入spec到数据库

---

### 2.4 执行转换并验证（生成Derived Layer / Silver）

**任务清单**：
- [ ] 2.4.1 开发转换执行引擎
  ```python
  def execute_transformations(db_path, study_code):
      """按依赖顺序执行所有转换SQL"""
      # 1. 读取transformation_rules
      # 2. 拓扑排序（按depends_on）
      # 3. 依次执行SQL
      # 4. 记录执行日志
  ```
- [ ] 2.4.2 执行D8318N00001的转换
- [ ] 2.4.3 QC转换结果
  - [ ] 抽样检查关键变量
  - [ ] 与手工计算对比
- [ ] 2.4.4 修正问题，迭代

**交付物**：
```
📁 scripts/
├── execute_transformations.py # 转换执行引擎
└── qc_transformations.py      # QC脚本
```

---

### 2.5 生成第一个Output（Output Layer / Gold）

**任务清单**：
- [ ] 2.5.1 开发Output生成器
  ```python
  def generate_output_data(db_path, output_id, study_code):
      """根据output_manifest生成查询，返回数据"""
  ```
- [ ] 2.5.2 开发R接口脚本
  ```r
  # generate_slides.R
  generate_output <- function(db_path, output_id) {
      # 1. 连接数据库
      # 2. 读取output_manifest
      # 3. 执行查询获取数据（或从Output View读取）
      # 4. 调用autoslider函数
  }
  ```
- [ ] 2.5.3 生成T1_demog（人口学表）
- [ ] 2.5.4 验证output正确性

**交付物**：
```
📁 scripts/
├── generate_output.py     # Python侧output生成
└── generate_slides.R      # R侧autoslider调用

📁 outputs/
└── D8318N00001/
    └── T1_demog.pptx
```

---

## Phase 3: Agent功能开发

### 3.1 依赖分析模块

**目标**：Agent能分析output需要哪些变量，哪些需要转换

**任务清单**：
- [ ] 3.1.1 开发依赖分析器
  ```python
  def analyze_output_dependencies(db_path, output_id):
      """
      返回：
      - required_vars: 需要的变量列表
      - missing_vars: 需要转换的变量
      - transformation_chain: 转换依赖链
      """
  ```
- [ ] 3.1.2 开发转换建议生成器
  ```python
  def suggest_transformation(var_name, structure, context):
      """为缺失的变量生成转换SQL建议"""
  ```
- [ ] 3.1.3 集成到工作流

---

### 3.2 SQL生成模块

**目标**：Agent能根据spec生成正确的SQL代码

**任务清单**：
- [ ] 3.2.1 开发SQL模板库
  - [ ] Static转换模板
  - [ ] Longitudinal转换模板（BASE, CHG, 窗口函数）
  - [ ] Occurrence flag模板
- [ ] 3.2.2 开发SQL生成器
  ```python
  def generate_transformation_sql(var_name, transformation_rule, context):
      """根据rule生成SQL"""
  ```
- [ ] 3.2.3 SQL验证器
  ```python
  def validate_sql(sql, db_path):
      """验证SQL语法和执行可行性"""
  ```

**SQL模板示例**：

```python
# sql_templates.py

TEMPLATES = {
    'aggregate_min': """
        SELECT {group_by}, MIN({source_col}) AS {target_col}
        FROM {source_table}
        {where_clause}
        GROUP BY {group_by}
    """,
    
    'aggregate_max': """
        SELECT {group_by}, MAX({source_col}) AS {target_col}
        FROM {source_table}
        {where_clause}
        GROUP BY {group_by}
    """,
    
    'baseline_value': """
        SELECT usubjid, aval AS {target_col}
        FROM raw_longitudinal
        WHERE paramcd = '{paramcd}' AND ablfl = 'Y'
    """,
    
    'change_from_baseline': """
        SELECT 
            m.*,
            b.aval AS base,
            m.aval - b.aval AS chg,
            CASE WHEN b.aval != 0 
                 THEN (m.aval - b.aval) / b.aval * 100 
                 ELSE NULL END AS pchg
        FROM raw_longitudinal m
        LEFT JOIN (
            SELECT usubjid, paramcd, aval
            FROM raw_longitudinal
            WHERE ablfl = 'Y'
        ) b ON m.usubjid = b.usubjid AND m.paramcd = b.paramcd
    """,
    
    'occurrence_flag': """
        CASE WHEN {condition} THEN 'Y' ELSE 'N' END AS {flag_name}
    """,
    
    'composite_sum': """
        SELECT usubjid, visit, '{paramcd}' AS paramcd, 
               '{param}' AS param, SUM(aval) AS aval
        FROM raw_longitudinal
        WHERE paramcd IN ({item_list})
        GROUP BY usubjid, visit
    """
}
```

---

### 3.3 复杂转换处理（Rule Document解析）

**目标**：Agent能读取复杂转换的Rule Document (markdown)并生成代码

**任务清单**：
- [ ] 3.3.1 定义Rule Document格式规范
- [ ] 3.3.2 开发Rule Document解析器
  ```python
  def parse_rule_document(md_path):
      """
      解析markdown，返回结构化信息：
      - business_rules: 业务规则
      - data_sources: 数据来源
      - calculation_steps: 计算步骤
      - validation_rules: 验证规则
      - reference_sql: 参考SQL（如果有）
      """
  ```
- [ ] 3.3.3 开发LLM集成（可选）
  ```python
  def generate_complex_sql_with_llm(parsed_rule_doc, context):
      """调用LLM生成复杂转换SQL"""
  ```

---

### 3.4 端到端流程集成

**目标**：实现从spec到output的完整自动化流程

**任务清单**：
- [ ] 3.4.1 开发主控脚本
  ```python
  # main_pipeline.py
  def run_pipeline(study_code, db_path):
      # 1. 加载spec (从数据库读取Catalog/Rules/Manifest)
      # 2. 分析依赖
      # 3. 执行转换 (Raw → Derived)
      # 4. 生成Output Views (Derived → Gold)
      # 5. 调用autoslider生成Output Files
  ```
- [ ] 3.4.2 开发CLI接口
  ```bash
  python main_pipeline.py --study D8318N00001 --db study.db --outputs all
  ```
- [ ] 3.4.3 日志和错误处理
- [ ] 3.4.4 执行报告生成

**交付物**：
```
📁 scripts/
├── main_pipeline.py       # 主控脚本
├── cli.py                 # 命令行接口
└── report_generator.py    # 执行报告生成
```

---

## Phase 4: 多Study推广

### 4.1 添加更多Study

**任务清单**：
- [ ] 4.1.1 添加D831AC00001 (IIM)
  - [ ] 解析ALS
  - [ ] 导入数据
  - [ ] 验证衍生
- [ ] 4.1.2 添加D831AC00002 (SSC)
  - [ ] 解析ALS
  - [ ] 导入数据
  - [ ] 验证衍生
- [ ] 4.1.3 处理Study间差异
  - [ ] 记录override需求
  - [ ] 完善output_study_config

---

### 4.2 完善知识库

**任务清单**：
- [ ] 4.2.1 扩展parameter_catalog
  - [ ] 添加更多疗效参数
  - [ ] 添加更多实验室参数
  - [ ] 标记indication适用性
- [ ] 4.2.2 标准化transformation_rules
  - [ ] 提取跨study通用规则
  - [ ] 建立最佳实践库
- [ ] 4.2.3 完善复杂转换的Rule Documents
  - [ ] 编写HAQDI.md
  - [ ] 编写其他复杂终点md

---

### 4.3 文档和培训

**任务清单**：
- [ ] 4.3.1 编写用户手册
  - [ ] 快速入门指南
  - [ ] Spec填写规范
  - [ ] 常见问题解答
- [ ] 4.3.2 编写开发者文档
  - [ ] 架构说明
  - [ ] API参考
  - [ ] 扩展指南
- [ ] 4.3.3 准备培训材料
  - [ ] PPT演示
  - [ ] 实操练习

**交付物**：
```
📁 docs/
├── user_guide.md          # 用户手册
├── developer_guide.md     # 开发者文档
├── spec_reference.md      # Spec填写参考
└── faq.md                 # 常见问题
```

---

## 项目文件结构

```
📁 autoslider_framework/
│
├── 📁 database/
│   ├── create_schema.sql
│   └── study_template.db
│
├── 📁 templates/
│   ├── spec_template.xlsx
│   └── spec_guide.md
│
├── 📁 scripts/
│   ├── import_spec.py
│   ├── parse_edc_schema.py
│   ├── import_raw.py
│   ├── execute_transformations.py
│   ├── generate_output.py
│   ├── main_pipeline.py
│   └── cli.py
│
├── 📁 r_scripts/
│   └── generate_slides.R
│
├── 📁 sql_templates/
│   ├── static_transformations.sql
│   ├── longitudinal_transformations.sql
│   └── occurrence_flags.sql
│
├── 📁 rule_docs/                  # 复杂转换的Rule Documents
│   ├── haqdi.md
│   ├── mmt8.md
│   └── ...
│
├── 📁 studies/
│   ├── 📁 D8318N00001/
│   │   ├── study.db
│   │   ├── spec.xlsx
│   │   ├── edc_schema/            # ALS文件
│   │   ├── raw/
│   │   └── outputs/
│   └── 📁 D831AC00001/
│       └── ...
│
├── 📁 docs/
│   ├── user_guide.md
│   └── developer_guide.md
│
├── requirements.txt
└── README.md
```

---

## 里程碑和时间估算

| 阶段 | 里程碑 | 主要交付物 |
|------|--------|-----------|
| **Phase 1** | 基础框架完成 | 数据库schema、Excel模板、导入脚本、ALS解析器 |
| **Phase 2** | 单Study验证通过 | D8318N00001完整流程跑通，生成第一个output |
| **Phase 3** | Agent功能可用 | 依赖分析、SQL生成、端到端pipeline |
| **Phase 4** | 多Study上线 | 3个study验证通过，文档完善 |

---

## 风险和应对

| 风险 | 可能性 | 影响 | 应对措施 |
|------|--------|------|----------|
| EDC Schema (ALS)格式不一致 | 中 | 高 | 设计灵活的解析器，支持配置化 |
| 复杂转换逻辑难以用SQL表达 | 中 | 中 | 允许外链Python函数作为补充 |
| autoslider集成问题 | 低 | 中 | 提前调研接口，准备备选方案 |
| 团队SQL学习曲线 | 中 | 低 | 提供模板和示例，减少手写SQL |

---

## 待决事项

- [ ] 确认raw数据的具体格式（SAS/CSV）
- [ ] 确认autoslider的具体函数接口
- [ ] 确认团队Python/R环境配置
- [ ] 确认是否需要Web界面（未来扩展）

---

## 术语对照表（完整版）

| 旧术语 | 新术语 | 说明 |
|--------|--------|------|
| Base layer | Raw Layer (Bronze) | 原始数据层 |
| Analysis layer | Derived Layer (Silver) | 衍生数据层 |
| - | Output Layer (Gold) | 输出层（视图） |
| snapshot | static | 截面数据 |
| measurement | longitudinal | 纵向数据 |
| event | occurrence | 事件数据 |
| data_dictionary | data_catalog | 变量目录 |
| param_pool | parameter_catalog | 参数知识库 |
| output_spec | output_manifest | 输出清单 |
| derivation_spec | transformation_rules | 转换规则 |
| spec_file / 外链md | rule_doc / Rule Document | 复杂转换说明文件 |
| ALS | EDC Schema | 数据库结构定义文件 |
| derivation | transformation | 转换/衍生 |
