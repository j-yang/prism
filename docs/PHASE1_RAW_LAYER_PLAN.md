# Phase 1: Raw Layer (Bronze) 实施计划

**目标**: 完成Raw Layer的设计和实现，能够从ALS解析并导入原始数据

---

## 任务总览

```
┌─────────────────────────────────────────────────────────────┐
│  1.1 设计 Raw Layer Schema                                  │
│      定义三张核心表的结构                                    │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  1.2 解析 ALS (EDC Schema)                                  │
│      从ALS提取Forms/Fields/Matrices信息                     │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  1.3 ALS → Raw Layer 映射                                   │
│      自动分类 + 生成data_catalog + 建表                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 1.1 设计 Raw Layer Schema

### 1.1.1 核心设计决策

**问题**: Raw Layer的三张表（raw_static, raw_longitudinal, raw_occurrence）应该是：
- A) 固定结构（预定义所有可能的列）
- B) 动态结构（根据ALS动态添加列）
- C) EAV模式（Entity-Attribute-Value，完全灵活）

**建议选择**: **B) 动态结构 + 核心列固定**

理由：
- 固定结构无法适应不同study的变量差异
- EAV模式查询复杂，性能差
- 动态结构保留核心列（usubjid, study_code等），其他列根据ALS动态生成

### 1.1.2 三张表的核心结构

#### raw_static（截面数据）
```
核心列（固定）:
├── usubjid        TEXT PRIMARY KEY
├── study_code     TEXT
└── import_timestamp TIMESTAMP

动态列（从ALS生成）:
├── age            INTEGER
├── sex            TEXT
├── race           TEXT
└── ... (根据ALS的static forms)
```

#### raw_longitudinal（纵向数据）
```
核心列（固定）:
├── id             INTEGER PRIMARY KEY
├── usubjid        TEXT
├── study_code     TEXT
├── paramcd        TEXT      -- 参数代码（核心）
├── param          TEXT      -- 参数标签
├── visit          TEXT      -- 访视名
├── visitnum       INTEGER   -- 访视序号
├── adt            TEXT      -- 分析日期
├── aval           REAL      -- 数值结果
├── avalc          TEXT      -- 字符结果
├── ablfl          TEXT      -- 基线标志
├── domain         TEXT      -- 来源标识
└── import_timestamp TIMESTAMP

索引:
├── idx_long_usubjid (usubjid)
├── idx_long_paramcd (paramcd)
└── idx_long_visit (visit)
```

#### raw_occurrence（事件数据）
```
核心列（固定）:
├── id             INTEGER PRIMARY KEY
├── usubjid        TEXT
├── study_code     TEXT
├── domain         TEXT      -- 事件类型（AE/CM/EC等）
├── seq            INTEGER   -- 序号
├── term           TEXT      -- 事件术语
├── decod          TEXT      -- 标准化术语
├── cat            TEXT      -- 类别
├── scat           TEXT      -- 子类别
├── astdt          TEXT      -- 开始日期
├── aendt          TEXT      -- 结束日期
└── import_timestamp TIMESTAMP

动态列（按domain不同）:
├── [AE专用] aesev, aeser, aerel, ...
├── [CM专用] cmdose, cmroute, ...
└── [EC专用] ecdose, ecroute, ...
```

### 1.1.3 待确定的设计问题

| 问题 | 选项 | 建议 |
|------|------|------|
| 日期存储格式 | TEXT (ISO8601) vs INTEGER (Unix timestamp) | TEXT，便于调试 |
| 多study是否共用表 | 单表（study_code区分）vs 每study独立表 | 单表，便于跨study分析 |
| raw_occurrence动态列 | 所有domain共用列 vs 按domain分子表 | 共用列，NULL填充 |

**需要你确认**: 上述建议是否符合你的预期？

---

## 1.2 解析 ALS (EDC Schema)

### 1.2.1 ALS文件结构分析

基于之前对ALS的分析，需要读取的sheet：

| Sheet | 用途 | 关键字段 |
|-------|------|----------|
| **Forms** | 表单定义 | OID, Name, Repeating |
| **Fields** | 字段定义 | FormOID, OID, Name, DataType, Length, CodeListOID |
| **Matrices** | 访视矩阵 | OID, Name, Addable |
| **Matrix#xxx** | 具体矩阵 | FormOID, 各Visit列 |
| **DataDictionaries** | 编码表 | OID, Name, DataType |
| **DataDictionaryEntries** | 编码值 | DataDictionaryOID, CodedValue, Decode |

### 1.2.2 解析器输出

```python
# 解析结果的数据结构
ParsedALS = {
    "study_info": {
        "study_code": str,
        "als_version": str,
        "als_file": str
    },
    "forms": [
        {
            "oid": str,
            "name": str,
            "repeating": bool,
            "fields": [...]
        }
    ],
    "fields": [
        {
            "form_oid": str,
            "oid": str,
            "name": str,
            "label": str,
            "data_type": str,  # TEXT, INTEGER, REAL, DATE
            "length": int,
            "codelist_oid": str,
            "codelist": dict   # {coded_value: decode}
        }
    ],
    "matrices": [
        {
            "oid": str,
            "name": str,
            "addable": bool,
            "forms": [form_oid, ...],
            "visits": [visit_name, ...]
        }
    ]
}
```

### 1.2.3 解析器任务分解

- [ ] 1.2.3.1 读取Forms sheet，提取表单基本信息
- [ ] 1.2.3.2 读取Fields sheet，提取字段定义
- [ ] 1.2.3.3 读取Matrices sheet，提取矩阵元数据
- [ ] 1.2.3.4 读取Matrix#xxx sheets，提取form-visit映射
- [ ] 1.2.3.5 读取DataDictionaries和Entries，提取编码表
- [ ] 1.2.3.6 关联Fields和CodeList，填充codelist字段
- [ ] 1.2.3.7 输出结构化的ParsedALS对象

---

## 1.3 ALS → Raw Layer 映射

### 1.3.1 自动分类逻辑

```
对每个Form:
    │
    ├─ 检查是否在任何Addable=True的Matrix中
    │   └─ 是 → occurrence
    │
    ├─ 检查出现在几个visit中
    │   ├─ >1个visit → longitudinal
    │   └─ =1个visit → static
    │
    └─ 特殊处理:
        ├─ 某些Form虽然多visit但属于static（如人口学在多个visit可编辑）
        └─ 需要人工审核确认
```

### 1.3.2 分类结果输出

```python
ClassificationResult = {
    "static_forms": [
        {"form_oid": str, "form_name": str, "confidence": "high/medium", "reason": str}
    ],
    "longitudinal_forms": [
        {"form_oid": str, "form_name": str, "paramcd_source": str, "confidence": "high/medium"}
    ],
    "occurrence_forms": [
        {"form_oid": str, "form_name": str, "domain": str, "confidence": "high"}
    ],
    "needs_review": [
        {"form_oid": str, "form_name": str, "reason": str}
    ]
}
```

### 1.3.3 生成 data_catalog

从分类结果生成data_catalog表：

```sql
INSERT INTO data_catalog (study_code, var_name, structure, label, data_type, source_form, source_field, codelist)
VALUES 
    ('D8318N00001', 'age', 'static', 'Age', 'INTEGER', 'DM', 'AGE', NULL),
    ('D8318N00001', 'sex', 'static', 'Sex', 'TEXT', 'DM', 'SEX', '{"M":"Male","F":"Female"}'),
    ...
```

### 1.3.4 动态建表

根据data_catalog动态生成DDL：

```python
def generate_raw_static_ddl(data_catalog: List[dict]) -> str:
    """
    输入: data_catalog中structure='static'的记录
    输出: CREATE TABLE raw_static (...)的SQL
    """
    
def generate_raw_occurrence_ddl(data_catalog: List[dict]) -> str:
    """
    输入: data_catalog中structure='occurrence'的记录
    输出: CREATE TABLE raw_occurrence (...)的SQL
    考虑: 按domain分组，合并所有domain的字段
    """
```

### 1.3.5 映射任务分解

- [ ] 1.3.5.1 实现分类函数 `classify_form(form, matrices)`
- [ ] 1.3.5.2 对ALS中所有form执行分类
- [ ] 1.3.5.3 生成分类报告供人工审核
- [ ] 1.3.5.4 人工审核后，生成data_catalog
- [ ] 1.3.5.5 根据data_catalog生成raw_static DDL
- [ ] 1.3.5.6 根据data_catalog生成raw_longitudinal DDL（核心列固定，无动态列）
- [ ] 1.3.5.7 根据data_catalog生成raw_occurrence DDL
- [ ] 1.3.5.8 执行DDL创建表
- [ ] 1.3.5.9 验证表结构

---

## 交付物清单

### 代码文件

```
📁 tools/
├── parse_als.py              # ALS解析器
├── classify_forms.py         # 表单分类器
├── generate_schema.py        # DDL生成器
└── init_raw_layer.py         # 初始化脚本（整合上述功能）
```

### 数据库文件

```
📁 database/
├── create_raw_layer.sql      # Raw Layer DDL（生成的）
└── study.db                  # SQLite数据库
```

### 输出报告

```
📁 reports/
├── als_parse_report.json     # ALS解析结果
├── classification_report.md  # 分类报告（供人工审核）
└── data_catalog.csv          # 变量目录导出
```

---

## 执行顺序

```
Step 1: 设计确认
        ├── 确认1.1中的设计决策
        └── 确认日期格式、多study策略等

Step 2: ALS解析器
        ├── 开发parse_als.py
        ├── 用D8318N00001 ALS测试
        └── 输出als_parse_report.json

Step 3: 表单分类
        ├── 开发classify_forms.py
        ├── 执行分类
        ├── 输出classification_report.md
        └── 人工审核并修正

Step 4: Schema生成
        ├── 开发generate_schema.py
        ├── 生成data_catalog
        ├── 生成DDL
        └── 创建数据库表

Step 5: 验证
        ├── 检查表结构
        ├── 手动插入测试数据
        └── 确认Raw Layer就绪
```

---

## 待讨论问题

1. **动态列的命名规范**: ALS中的字段名是否直接作为列名？还是需要映射？
   - 例如: ALS中`BRTHDAT` → 数据库中`brthdat`还是`birth_date`？

2. **Longitudinal的PARAMCD来源**: 
   - 对于实验室数据，PARAMCD通常来自`LBTESTCD`
   - 对于生命体征，PARAMCD通常来自`VSTESTCD`
   - 如何确定哪个字段作为PARAMCD？

3. **Occurrence的domain识别**:
   - AE/CM/EC等domain如何从ALS中识别？
   - 是根据Form名称推断，还是需要人工指定？

4. **分类的人工介入点**:
   - 分类报告的格式是什么？
   - 人工修正后如何反馈回系统？

---

## 下一步

请确认：
1. 上述设计思路是否符合预期？
2. 有哪些待讨论问题需要先确定？
3. 是否可以开始Step 1（设计确认）？
