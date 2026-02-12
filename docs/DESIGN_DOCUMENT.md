# Multi-Study Clinical Data Analysis Framework
# 多研究临床数据分析框架 - 最终设计文档

**讨论日期**: 2026-02-05 至 2026-02-11
**状态**: 设计定稿

---

## 术语表 (Terminology)

| 类别 | 术语 | 定义 |
|------|------|------|
| **数据层级** | | |
| | Raw Layer (Bronze) | 原始数据层，从EDC直接导入 |
| | Derived Layer (Silver) | 衍生数据层，包含计算和转换后的分析数据 |
| | Output Layer (Gold) | 输出层，面向报表的聚合视图 |
| **数据结构** | | |
| | static | 截面数据，1 row per subject |
| | longitudinal | 纵向数据，1 row per subject × param × visit |
| | occurrence | 事件数据，1 row per event |
| **元数据** | | |
| | Schema | 数据库结构定义 (DDL) |
| | Data Catalog | 变量目录/数据字典 |
| | Parameter Catalog | 参数知识库 |
| | Output Manifest | 输出定义清单 |
| | Transformation Rule | 衍生/转换规则 |

---

## 一、核心设计理念

### 1.1 三层数据结构（按时间语义分类）

放弃传统的ADaM domain命名，采用更本质的数据结构分类：

| 数据结构 | 语义 | 记录粒度 | 传统对应 |
|----------|------|----------|----------|
| **static** | 截面数据 | 一人一条 | ADSL |
| **longitudinal** | 纵向数据 | 一人×参数×时点 | BDS (ADLB/ADVS/ADEG) |
| **occurrence** | 事件发生 | 一事件一条 | OCCDS (ADAE/ADCM) |

**为什么这样分**：
- 只有3种结构，概念极简
- 每种结构对应一类操作（加变量/加参数/加flag）
- 与autoslider函数天然对应
- Agent只需掌握3种代码模板

### 1.2 三层数据层级 (Medallion Architecture)

```
Raw Layer (Bronze)     → 原始数据，从EDC直接导入，确定性ETL
                         ↓
Derived Layer (Silver) → 衍生数据，包含计算和转换
                         ↓
Output Layer (Gold)    → 输出视图，面向报表的聚合数据
                         ↓
Output Files           → PPT/Excel文件（文件系统，非DB）
```

### 1.3 Output-Driven设计

```
起点是Output（要出什么表/图）
    ↓
倒推需要什么变量/参数
    ↓
确定哪些需要衍生
    ↓
生成衍生代码
```

不是先定义所有变量，而是**按需衍生**。

### 1.4 ALS作为Ground Truth（EDC Schema）

ALS（CRF Draft）文件定义了raw数据的结构，确定性ETL脚本可以：
- 自动识别哪些form是static/longitudinal/occurrence
- 推断变量名和数据类型
- 建立raw到分析变量的映射

**注意**：Raw Layer的ETL是确定性脚本，不需要AI Agent。Agent能力应集中在Derived Layer。

---

## 二、技术选型

### 2.1 数据库：SQLite

| 决策 | 理由 |
|------|------|
| 选择SQLite而非DuckDB | 更成熟、文档丰富、团队易接受 |
| 单文件数据库 | 便于分发和版本管理 |
| 数据+元数据在一起 | 一个.db文件包含一切 |

### 2.2 语言分工

```
Python: 胶水语言
  - 解析ALS
  - 解析spec（Excel → 数据库）
  - 执行SQL
  - AI Agent交互

SQL: 数据操作语言
  - 所有衍生逻辑用SQL表达
  - Agent生成SQL代码（准确率最高）

R: 输出生成
  - 调用autoslider生成表/图
  - 从数据库读取数据
```

### 2.3 Spec格式

```
Excel (人类编辑) → 导入 → SQLite (机器读取)
```

不使用YAML，数据库本身就是结构化存储。

---

## 三、数据库结构

```
study.db (单文件，包含一切)
│
├── 元数据表 (Metadata / Catalog)
│   ├── studies              -- 研究列表和元数据
│   ├── data_catalog         -- 变量目录（从ALS生成）
│   ├── transformation_rules -- 衍生/转换规则
│   ├── parameter_catalog    -- 参数知识库
│   └── output_manifest      -- 输出定义清单
│
├── Raw Layer (Bronze) - 从EDC导入
│   ├── raw_static           -- 截面数据
│   ├── raw_longitudinal     -- 纵向数据
│   └── raw_occurrence       -- 事件数据
│
├── Derived Layer (Silver) - 衍生结果
│   ├── derived_static       -- raw + 衍生变量
│   ├── derived_longitudinal -- raw + 衍生参数
│   └── derived_occurrence   -- raw + 事件flag
│
└── Output Layer (Gold) - 输出视图
    └── output_views         -- 面向报表的聚合视图
```

---

## 四、Schema设计（元数据表结构）

### 4.1 studies（研究元数据）

| 字段 | 类型 | 说明 |
|------|------|------|
| study_code | TEXT PK | 研究代码 |
| indication | TEXT | 适应症 |
| als_file | TEXT | EDC Schema文件路径 |
| status | TEXT | active/completed |

### 4.2 data_catalog（变量目录）

| 字段 | 类型 | 说明 |
|------|------|------|
| var_name | TEXT | 变量名 |
| structure | TEXT | static/longitudinal/occurrence |
| label | TEXT | 变量标签 |
| type | TEXT | 数据类型 |
| source | TEXT | 来源（als:FORM.FIELD） |
| codelist | TEXT | 编码值（JSON） |

### 4.3 transformation_rules（转换规则）

| 字段 | 类型 | 说明 |
|------|------|------|
| var_name | TEXT | 变量名 |
| structure | TEXT | static/longitudinal/occurrence |
| depends_on | TEXT | 依赖的变量（逗号分隔） |
| transformation_sql | TEXT | SQL表达式或脚本引用 |
| description | TEXT | 业务说明 |
| complexity | TEXT | simple/medium/complex |
| rule_doc | TEXT | 复杂衍生的外链md文件 |

### 4.4 parameter_catalog（参数知识库）

| 字段 | 类型 | 说明 |
|------|------|------|
| paramcd | TEXT PK | 参数代码 |
| param | TEXT | 参数标签 |
| category | TEXT | lab/efficacy/vital |
| indication | TEXT | 适用适应症 |
| derivation_type | TEXT | direct/composite/complex |
| source_form | TEXT | 来源CRF表单 |
| transformation_sql | TEXT | 衍生SQL（如果需要） |
| rule_doc | TEXT | 复杂参数的外链md |

### 4.5 output_manifest（输出清单）

| 字段 | 类型 | 说明 |
|------|------|------|
| output_id | TEXT PK | 输出标识 |
| output_type | TEXT | table/figure/listing |
| source_structure | TEXT | static/longitudinal/occurrence |
| columns | TEXT | 需要的列（逗号分隔） |
| filter | TEXT | WHERE条件 |
| param_filter | TEXT | PARAMCD过滤（longitudinal用） |
| group_by | TEXT | 分组变量 |
| autoslider_func | TEXT | R函数名 |
| title | TEXT | 标题模板 |
| footnote | TEXT | 脚注模板 |
| studies | TEXT | 适用的study（逗号分隔，空=全部） |

---

## 五、三种转换操作

### 5.1 Static: 加变量

```sql
-- 衍生TRTSDT（首次给药日期）
SELECT usubjid, MIN(astdt) AS trtsdt
FROM raw_occurrence
WHERE domain = 'EC'
GROUP BY usubjid

-- 衍生SAFFL（安全集标志）
CASE WHEN trtsdt IS NOT NULL THEN 'Y' ELSE 'N' END AS saffl

-- 衍生BL_PHGA（基线PHGA）
SELECT usubjid, aval AS bl_phga
FROM raw_longitudinal
WHERE paramcd = 'PHGA' AND ablfl = 'Y'
```

### 5.2 Longitudinal: 加参数

```sql
-- 新增组合参数MMT8（8个item求和）
INSERT INTO derived_longitudinal (usubjid, paramcd, param, visit, aval)
SELECT 
    usubjid,
    'MMT8' AS paramcd,
    'MMT-8 Total Score' AS param,
    visit,
    SUM(aval) AS aval
FROM raw_longitudinal
WHERE paramcd LIKE 'MMT_ITEM%'
GROUP BY usubjid, visit

-- 衍生BASE和CHG
SELECT 
    *,
    FIRST_VALUE(aval) OVER (PARTITION BY usubjid, paramcd ORDER BY visitnum) AS base,
    aval - base AS chg
FROM raw_longitudinal
```

### 5.3 Occurrence: 加Flag

```sql
-- 衍生TEAEFL（治疗期不良事件标志）
UPDATE derived_occurrence
SET teaefl = CASE 
    WHEN astdt BETWEEN trtsdt AND trtedt + 28 THEN 'Y' 
    ELSE 'N' 
END
WHERE domain = 'AE'

-- 衍生SAEFL（严重不良事件标志）
UPDATE derived_occurrence
SET saefl = CASE WHEN aeser = 'Y' THEN 'Y' ELSE 'N' END
WHERE domain = 'AE'
```

---

## 六、完整工作流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 1: 解析EDC Schema (ALS)                                               │
│  确定性脚本解析ALS文件，生成data_catalog初稿                                  │
│  自动识别static/longitudinal/occurrence分类                                  │
│  【无需Agent，纯规则驱动】                                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 2: 导入Raw数据到Raw Layer (Bronze)                                    │
│  EDC数据导入到raw_static/raw_longitudinal/raw_occurrence                    │
│  【无需Agent，确定性ETL】                                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 3: 填写output_manifest (人工)                                         │
│  定义要生成的表/图，需要的变量和过滤条件                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 4: Agent分析依赖                                                      │
│  根据output_manifest分析：哪些变量需要衍生？依赖关系是什么？                   │
│  【Agent介入点1】                                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 5: 填写/确认transformation_rules (人工+Agent建议)                     │
│  简单转换：Agent自动生成SQL                                                  │
│  复杂转换：引用外部Rule Document (markdown)                                  │
│  【Agent介入点2】                                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 6: 执行转换，生成Derived Layer (Silver)                               │
│  按依赖顺序执行SQL，生成derived_*表                                          │
│  ← QC点1：验证衍生变量的正确性                                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 7: 生成Output Layer (Gold) + Output Files                             │
│  根据output_manifest生成Output Views                                        │
│  R读取数据，调用autoslider生成表/图                                          │
│  ← QC点2：验证输出的正确性                                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 七、文件结构

```
📁 project/
├── spec.xlsx                    # 人类编辑的spec（Excel模板）
│   ├── Sheet: studies
│   ├── Sheet: transformation_rules
│   ├── Sheet: parameter_catalog
│   └── Sheet: output_manifest
│
├── study.db                     # SQLite数据库（数据+元数据）
│
├── rule_docs/                   # 复杂转换的Rule Documents
│   ├── haqdi.md
│   ├── sledai.md
│   └── mmt8.md
│
├── edc_schema/                  # EDC Schema文件 (ALS)
│   └── D8318N00001_V1.0.xlsx
│
├── generated_code/              # Agent生成的代码
│   ├── transform_static.sql
│   ├── transform_longitudinal.sql
│   ├── transform_occurrence.sql
│   └── generate_outputs.R
│
└── outputs/                     # 生成的表/图（Output Files）
    ├── T1_demog.pptx
    └── F1_efficacy.pptx
```

---

## 八、Rule Document格式（复杂转换）

对于complexity='complex'的转换，使用外链Rule Document（markdown文件）：

```markdown
# [参数名称]

## 业务规则
1. 规则1...
2. 规则2...
3. 缺失处理...

## 数据来源
- Form: xxx
- 字段: yyy, zzz

## 计算步骤
### Step 1: xxx
### Step 2: xxx

## 验证规则
- 范围检查...
- 逻辑检查...

## 参考SQL
```sql
-- Agent可参考的SQL示例
```
```

---

## 九、Agent的职责边界

| 任务 | 需要Agent? | Agent做什么 | 人做什么 |
|------|------------|-------------|----------|
| 解析EDC Schema | ❌ | - | 确定性脚本执行，人工审核分类 |
| 导入Raw数据 | ❌ | - | 确定性ETL执行 |
| 分析output依赖 | ✅ | 识别需要转换的变量 | 确认分析结果 |
| 简单转换 | ✅ | 自动生成SQL | 审核代码 |
| 复杂转换 | ✅ | 读取Rule Document，生成SQL | 编写Rule Document，审核代码 |
| 生成output | ✅ | 生成查询SQL，调用autoslider | QC最终结果 |

**关键原则**：Agent能力集中在Derived Layer（Silver），Raw Layer（Bronze）保持确定性。

---

## 十、跨Study管理

### 10.1 矩阵式配置

output_manifest和transformation_rules支持study列：

```
| output_id | columns | filter | D8318N001 | D831AC001 | D831AC002 |
|-----------|---------|--------|-----------|-----------|-----------|
| T1_demog  | AGE,SEX | SAFFL  | ✓         | ✓         | ✓         |
| T2_effic  | BL_PHGA | SAFFL  | ✓         | ✓         | -         |
```

- `✓` = 使用默认配置
- `-` = 该study不需要
- 具体值 = 覆盖默认

### 10.2 Indication级别的参数管理

parameter_catalog按indication标记：
- `COMMON`: 所有indication通用
- `IIM`: IIM特有
- `SSC`: SSC特有
- `IIM,SSC`: 多个indication共享

---

## 十一、与autoslider集成

| 数据结构 | autoslider函数 |
|----------|---------------|
| static | t_dm_slide, gt_t_dm_slide |
| longitudinal | g_lb_slide, g_vs_slide, g_eg_slide |
| occurrence | t_ae_summ_slide, t_ae_pt_slide, l_ae_slide |

R代码示例：
```r
library(DBI)
library(RSQLite)
library(autoslider.core)

con <- dbConnect(SQLite(), "study.db")

# 读取数据（从Output View或直接从Derived Layer）
demog_data <- dbGetQuery(con, "
    SELECT age, sex, race, trta 
    FROM derived_static 
    WHERE saffl = 'Y'
")

# 生成表格
t_dm_slide(demog_data, ...)
```

---

## 十二、下一步行动

### Phase 1: 基础框架搭建
- [ ] 创建SQLite数据库schema
- [ ] 开发Excel→SQLite导入脚本
- [ ] 开发EDC Schema (ALS)解析器

### Phase 2: 单Study验证
- [ ] 用D8318N00001验证完整流程
- [ ] 手动填写spec
- [ ] 生成一个output

### Phase 3: Agent功能开发
- [ ] 实现依赖分析
- [ ] 实现SQL生成
- [ ] 实现autoslider调用

### Phase 4: 多Study推广
- [ ] 添加更多study
- [ ] 完善parameter_catalog
- [ ] 文档化规范

---

## 附录：关键决策记录

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 数据层级 | Raw/Derived/Output (Bronze/Silver/Gold) | 业界标准Medallion架构 |
| 数据结构 | static/longitudinal/occurrence | 按时间语义分类，概念极简 |
| 数据库 | SQLite | 成熟稳定，团队易接受 |
| 转换语言 | SQL | Agent生成准确率最高 |
| 胶水语言 | Python | AI生态好，可调用R |
| 输出工具 | autoslider (R) | 项目要求 |
| Spec格式 | Excel编辑→SQLite存储 | 人类友好+机器友好 |
| 复杂逻辑 | Rule Document (Markdown) | 无字符限制，Git友好 |
| Raw Layer ETL | 确定性脚本，无Agent | 规则明确，可重复，易调试 |
