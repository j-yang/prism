# PRISM-DB Development Log

## 项目概述

PRISM-DB 是一个临床试验数据仓库，基于 DuckDB 实现 Medallion 三层架构 (Bronze/Silver/Gold)，并集成 AI Agent 进行代码生成。

---

## 已完成的工作

### Phase 1: Meta Schema v3.1 (2026-02-13)

**目标**: 建立统一的元数据管理

**产出**:
- `sql/init_meta.sql` - 11 张 meta 表 DDL
- `src/prismdb/schema/models.py` - Pydantic 模型
- `src/prismdb/metadata.py` - MetadataManager 类

**Meta 表结构**:

| 类别 | 表名 | 用途 |
|------|------|------|
| 参考库 | `meta.params` | Longitudinal 参数定义 (可外链) |
| | `meta.flags` | Occurrence 事件标志 (可外链) |
| | `meta.visits` | 分析用 Visit (可外链) |
| Study-specific | `meta.study_info` | 研究基本信息 |
| | `meta.variables` | 统一变量注册表 |
| | `meta.derivations` | 衍生规则 |
| | `meta.outputs` | 输出定义 (table/listing/figure) |
| | `meta.output_variables` | 输出-变量关联 |
| | `meta.output_params` | 输出-参数关联 |
| | `meta.functions` | 复杂函数库 |
| | `meta.dependencies` | 变量依赖关系 |

---

### Phase 2: Silver Layer Generator (2026-02-14)

**目标**: 从 meta.derivations 生成 Silver 层 SQL

**产出**:
- `src/prismdb/silver/generator.py` - SilverGenerator 类
- 硬编码模板 (6 种)
- DeepSeek API 集成

**模板模式**:
| 模板 | 匹配规则 | 示例 |
|------|---------|------|
| `date_min` | MIN, earliest, first + date | `SELECT usubjid, MIN(exstdt) AS trtsdt` |
| `flag_case` | CASE WHEN, flag, Y/N | `CASE WHEN x THEN 'Y' ELSE 'N' END` |
| `age_group` | age group, agegrp, 18-64 | `CASE WHEN age < 65 THEN '18-64' ... END` |
| `direct_copy` | Take, Equal to, 取 | `SELECT col AS target FROM table` |
| `concat` | concat, Concatenate | `SELECT col1 || col2 AS target` |
| `change_baseline` | change, chg, baseline | `FIRST_VALUE(aval) OVER (...)` |

**输出**:
```
generated/
├── derive_baseline.sql
├── derive_occurrence.sql
├── derive_longitudinal.sql
└── generation_log.json
```

---

### Phase 3: Gold Layer Engine (2026-02-14)

**目标**: 从 meta.outputs 生成统计计算脚本

**产出**:
- `sql/init_gold.sql` - 3 张 Gold 表 DDL
- `src/prismdb/gold/engine.py` - GoldEngine 类
- `src/prismdb/gold/stats.py` - 统计函数库

**Gold 表结构** (长表设计):

```sql
gold.baseline (
    output_id,        -- 输出 ID
    group1_name,      -- 分组变量 (如 'TRTA')
    group1_value,     -- 分组值 (如 'Drug A')
    variable,         -- 变量名 (如 'AGE', 'SEX')
    category,         -- 分类值 (可空)
    stat_name,        -- 统计量 ('n', 'mean', 'sd', 'pct')
    stat_value,       -- 统计值
    stat_display      -- 格式化显示值
)
```

**统计函数**:
- `desc_stats_continuous()` - 连续变量: n, mean, sd, median, min, max
- `desc_stats_categorical()` - 分类变量: category, n, pct
- `format_stat()` - 格式化输出

**输出**:
```
generated/analysis/
├── T1_demog.py        # 人口学表脚本
├── T4_teae.py         # AE 汇总脚本
└── analysis_log.json
```

---

## 文件结构

```
prism-db/
├── src/prismdb/
│   ├── __init__.py           # 包入口
│   ├── database.py           # Database 连接类
│   ├── metadata.py           # MetadataManager
│   ├── parse_als_v2.py       # ALS 解析器
│   ├── classify_forms_v2.py  # Form 分类器
│   ├── init_bronze.py        # Bronze 数据导入
│   ├── schema/
│   │   ├── __init__.py
│   │   └── models.py         # Pydantic 模型
│   ├── silver/
│   │   ├── __init__.py
│   │   └── generator.py      # Silver SQL 生成器
│   └── gold/
│       ├── __init__.py
│       ├── engine.py         # Gold 分析脚本生成器
│       └── stats.py          # 统计函数
├── sql/
│   ├── init_meta.sql         # Meta DDL (11 表)
│   └── init_gold.sql         # Gold DDL (3 表)
├── tests/
│   ├── test_phase1.py        # Meta 表测试
│   ├── test_phase1_3.py      # ALS 解析测试
│   ├── test_silver_generator.py
│   └── test_gold_engine.py
├── examples/
│   └── some_study/
│       └── Raw to TLF spec 1 (1).xlsx
├── .env                      # 环境变量
├── requirements.txt
└── ARCHITECTURE.md           # 架构设计文档 v3.1
```

---

## API 集成

### DeepSeek API

```python
# .env
DEEPSEEK_API_KEY=sk-xxx

# 使用
gen = SilverGenerator(db, api_key="sk-xxx")
gen = GoldEngine(db, api_key="sk-xxx")
```

**API 调用位置**:
- `src/prismdb/silver/generator.py:258` - `_call_llm()`
- `src/prismdb/gold/engine.py:472` - `_call_llm()`

---

## 数据流

```
┌─────────────────────────────────────────────────────────────────────┐
│  Input                                                              │
│  ├── D8318N00001_ALS.xlsx (EDC Schema)                             │
│  └── Raw to TLF spec.xlsx (Mapping Spec)                            │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Bronze Layer (Raw Data)                                            │
│  ├── parse_als_to_db() → bronze.demog, bronze.ae, ...              │
│  └── meta.variables 填充                                            │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Silver Layer (Subject Level)                                       │
│  ├── SilverGenerator.generate_all()                                │
│  ├── 输出: generated/derive_*.sql                                   │
│  └── 用户执行 SQL → silver.baseline, silver.occurrence, ...        │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Gold Layer (Group Level)                                           │
│  ├── GoldEngine.generate_all()                                     │
│  ├── 输出: generated/analysis/*.py                                  │
│  └── 用户执行 Python → gold.baseline, gold.occurrence, ...         │
└─────────────────────────────────────────────────────────────────────┘
```

---

### Phase 4: Traceability Schema (2026-02-14)

**目标**: 实现数据溯源 (Gold → Silver → Bronze)

**产出**:
- `sql/init_traceability.sql` - 2 张追溯表 DDL

**表结构**:
```sql
meta.data_lineage (
    target_output_id,    -- T1_demog
    target_group_value,  -- Drug A
    target_variable,     -- AGE
    target_stat_name,    -- mean
    source_table,        -- silver.baseline
    source_subjects      -- JSON: ["001", "002", ...]
)

meta.silver_sources (
    target_table,        -- silver.baseline
    target_column,       -- AGE
    source_table,        -- bronze.demog
    source_column,       -- BRTHDT
    derivation_rule      -- 计算逻辑
)
```

---

### Phase 5: Platinum Portal (2026-02-14)

**目标**: Web 端数据查看门户

**产出**:
- `src/prismdb/platinum/generator.py` - PlatinumGenerator 打包器
- `src/prismdb/platinum/static/index.html` - Portal HTML
- `src/prismdb/platinum/static/style.css` - Academic 风格 CSS
- `src/prismdb/platinum/static/app.js` - DuckDB WASM 查询
- `scripts/run_mvp_pipeline.py` - 端到端 MVP 脚本

**架构决策**:
- 使用 DuckDB WASM 在浏览器端运行 SQL
- 不嵌入数据，通过 HTTP 加载 .duckdb 文件
- 支持点击数字查看 Traceability

**DuckDB WASM 问题**:
- Safari CORS 限制导致 Worker 加载失败
- 尝试方案:
  1. unpkg CDN → MIME type 错误
  2. jsdelivr CDN → 同样 CORS 问题
  3. ES6 module import + v0.10.0 → 待验证

---

## 待完成的工作

### 短期 (MVP 完善)

- [ ] 修复 DuckDB WASM 加载问题
- [ ] 真实 Spec 数据测试
- [ ] 部署到内网服务器

### 中期

- [ ] rule_docs/*.md 读取功能
- [ ] 假设检验 (p-value) 支持
- [ ] 更多统计模板

### 长期

- [ ] CLI 工具 (`prism generate silver/gold`)
- [ ] 图表渲染 (Platinum 层)
- [ ] R 引擎支持

---

## 关键设计决策

1. **长表 vs 宽表**: Gold 层采用长表设计，便于新增统计量、支持稀疏数据
2. **模板 + LLM**: 简单模式用模板，复杂模式用 LLM，降低 API 成本
3. **生成脚本 vs 直接执行**: 生成可审查的代码文件，用户手动执行，保证可控性
4. **纯 Python 统计**: MVP 阶段用 numpy/pandas，后续可扩展 scipy/statsmodels
5. **环境变量管理**: API Key 等敏感信息通过 `.env` 管理

---

## 测试命令

```bash
# Meta 表测试
pytest tests/test_phase1.py -v

# Silver 生成器测试
pytest tests/test_silver_generator.py -v

# Gold 引擎测试
pytest tests/test_gold_engine.py -v

# 手动执行生成的脚本
python generated/analysis/T1_demog.py
```

---

## 更新记录

| 日期 | 版本 | 内容 |
|------|------|------|
| 2026-02-13 | v3.1 | Meta Schema 重构 (5 表 → 11 表) |
| 2026-02-14 | v3.2 | Silver Generator MVP |
| 2026-02-14 | v3.3 | Gold Engine MVP |
| 2026-02-14 | v3.4 | Traceability Schema |
| 2026-02-14 | v3.5 | Platinum Portal (DuckDB WASM) |
