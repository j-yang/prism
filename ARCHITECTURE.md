# PRISM Architecture

## Overview

PRISM is a clinical trial data warehouse built on DuckDB with AI-powered code generation.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     meta (Specification)                    │
│  10 tables: study_info, visits, form_classification,        │
│  bronze_dictionary, params, attrs, silver_dictionary,       │
│  gold_dictionary, platinum_dictionary, dependencies         │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    Bronze (Raw Data)                        │
│  One table per form: bronze.ae, bronze.cm, bronze.dm, ...   │
│  Minimal processing: lowercase columns, date conversion     │
└──────────────────────────┬──────────────────────────────────┘
                           │ Agent generates SQL
┌──────────────────────────▼──────────────────────────────────┐
│                    Silver (Derived)                         │
│  3 schemas: silver.baseline, silver.longitudinal,           │
│             silver.occurrence                               │
└──────────────────────────┬──────────────────────────────────┘
                           │ Agent generates Python
┌──────────────────────────▼──────────────────────────────────┐
│                    Gold (Statistics)                        │
│  3 schemas: gold.baseline, gold.longitudinal,               │
│             gold.occurrence                                 │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                   Platinum (Deliverables)                   │
│  Output: RTF, PDF, HTML, Slides                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Meta Schema (10 Tables)

### Study Configuration
| Table | Purpose |
|-------|---------|
| `meta.study_info` | Study 基本信息 |
| `meta.visits` | 分析 Visit 定义 |

### Data Dictionary
| Table | Purpose |
|-------|---------|
| `meta.bronze_dictionary` | Bronze 层数据字典（来自 ALS） |
| `meta.silver_dictionary` | Silver 层数据字典（来自 Spec） |
| `meta.gold_dictionary` | Gold 层数据字典（来自 Spec） |
| `meta.platinum_dictionary` | Platinum 交付物定义 |

### Form & Variable Classification
| Table | Purpose |
|-------|---------|
| `meta.form_classification` | Form → Domain/Schema 映射 |
| `meta.params` | Longitudinal 参数定义 |
| `meta.attrs` | Occurrence 扩展字段定义 |

### Dependencies
| Table | Purpose |
|-------|---------|
| `meta.dependencies` | 变量依赖关系 |

---

## Bronze Layer

### Design Principle

**按原始 Form 存储，保持完整 Traceability**

```
bronze.ae    -- Adverse Events
bronze.cm    -- Concomitant Medications
bronze.dm    -- Demographics
bronze.lb    -- Laboratory
bronze.vs    -- Vital Signs
... (N tables, one per form)
```

### Processing Rules

1. **列名小写**：`AETERM` → `aeterm`
2. **日期转换**：SAS date → DATE type
3. **保留所有字段**：不做筛选
4. **可选删除**：用户可指定删除不需要的列

### Example

```sql
CREATE TABLE bronze.ae (
    usubjid TEXT NOT NULL,
    subjid TEXT,
    aeterm TEXT,
    aestdtc DATE,
    aeendtc DATE,
    aesoc TEXT,
    aedecod TEXT,
    aeout TEXT,
    aeser TEXT,
    ... (all AE fields)
);
```

### Traceability

```
bronze_dictionary:
  var_name | form_oid | schema      | var_label
  ---------|----------|-------------|------------
  aeterm   | ae       | occurrence  | Adverse Event
  age      | dm       | baseline    | Age
  sysbp    | vs       | longitudinal| Systolic BP
```

---

## Silver Layer

3 schemas with consistent structure:

### baseline
- One row per subject
- Derived from bronze baseline forms

### longitudinal
- One row per subject per visit
- Derived from bronze longitudinal forms

### occurrence
- One row per event
- Consolidated from AE, CM, MH, PR forms
- Structure: `usubjid, subjid, domain, seq, term, startdt, enddt, coding_high, coding_low, flags JSON, attrs JSON`

---

## Gold Layer

### Gold Schema (3 Tables)

| Table | Purpose |
|-------|---------|
| `gold.baseline` | Group-level baseline statistics |
| `gold.longitudinal` | Group-level longitudinal statistics |
| `gold.occurrence` | Group-level occurrence statistics |

### Gold Table Structure

每行 = 一个 group + 一个 element + 一个 selection + 统计量JSON

```sql
-- gold.baseline
deliverable_id, element_id, group_id, statistics(JSON)

-- gold.longitudinal  
deliverable_id, element_id, group_id, visit, statistics(JSON)

-- gold.occurrence
deliverable_id, element_id, group_id, selection, statistics(JSON)
```

示例数据：
```json
// gold.baseline - 连续变量
{"n": 50, "mean": 45.2, "sd": 12.3, "median": 44.0}

// gold.baseline - 分类变量
{"n": 30, "pct": 60.0}

// gold.occurrence - 事件统计
{"n_subjects": 10, "n_events": 15, "pct": 20.0}
```

---

## Data Flow

```
1. ALS 解析
   parse_als_to_db() → bronze tables, meta.bronze_dictionary

2. Spec 解析
   parse_spec_to_db() → meta.params, meta.silver_dictionary, meta.gold_dictionary

3. Bronze 数据加载
   load_sas_to_bronze() → bronze.* tables

4. Silver 生成
   SilverGenerator.generate() → silver.* tables

5. Gold 生成
   GoldEngine.generate() → gold.* tables

6. Platinum 渲染
   render_output() → RTF/PDF/HTML
```

---

## Agent System

### Code Generation Flow

```
meta.silver_dictionary (transformation) ──▶ Template Match? ──▶ Yes ──▶ Jinja2 Template
                                                 │
                                                 No
                                                 │
                                                 ▼
                                    DeepSeek LLM ──▶ Generated SQL/Python
                                                 │
                                                 ▼
                                    Needs Review (flagged)
```

### Template Types

| Template | Pattern | Example |
|----------|---------|---------|
| direct_copy | "Take", "Equal to" | `SELECT col AS target` |
| coalesce | "Coalesce" | `COALESCE(col1, col2)` |
| recode | "Recode", "Map" | `CASE WHEN...` |
| date_diff | "Date diff" | `DATE_DIFF(day, d1, d2)` |
| combine | "Combine", "Concat" | `CONCAT(a, b)` |
| flag | "Flag", "Y/N" | `CASE WHEN cond THEN 'Y'` |

---

## File Organization

```
src/prism/
├── core/
│   ├── database.py      # DuckDB connection wrapper
│   ├── schema.py        # Pydantic models
│   └── config.py        # Path helpers
│
├── sql/
│   ├── init_meta.sql    # Meta schema DDL
│   └── init_bronze.sql  # Bronze schema template
│
├── agent/
│   ├── llm.py           # DeepSeek API wrapper
│   └── templates/       # Jinja2 templates
│
├── meta/
│   ├── manager.py       # MetadataManager class
│   └── als_parser.py    # ALS file parser
│
├── bronze/
│   └── loader.py        # SAS/CSV import
│
├── silver/
│   └── generator.py     # SQL generation
│
├── gold/
│   ├── engine.py        # Python script generation
│   └── stats.py         # Statistical functions
│
└── platinum/
    └── renderer.py      # Report rendering
```

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| Database | DuckDB |
| Language | Python 3.12 |
| Data Models | Pydantic v2 |
| Templates | Jinja2 |
| LLM | DeepSeek API |
| Stats | NumPy/Pandas |
