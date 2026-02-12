# Multi-Study Clinical Data Analysis Framework
# 项目实施计划

---

## 项目概览

| 项目名称 | 多研究临床数据分析框架 |
|---------|----------------------|
| 目标 | 建立基于数据库的自动化数据处理流程，支持AI Agent生成转换代码 |
| 技术栈 | SQLite + Python + SQL + R/autoslider |
| 试点研究 | D8318N00001 (IIM/SSC) |

## 术语速查

| 术语 | 含义 |
|------|------|
| Raw Layer (Bronze) | 原始数据层 |
| Derived Layer (Silver) | 衍生数据层 |
| Output Layer (Gold) | 输出层（视图） |
| static | 截面数据 (1 row/subject) |
| longitudinal | 纵向数据 (1 row/subject×param×visit) |
| occurrence | 事件数据 (1 row/event) |
| data_catalog | 变量目录 |
| parameter_catalog | 参数知识库 |
| output_manifest | 输出清单 |
| transformation_rules | 转换规则 |
| Rule Document | 复杂转换的markdown说明文件 |

---

## Phase 1: 基础框架搭建

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
