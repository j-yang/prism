# ALS Parser 改造计划

## 目标

将 ALS (Annotated Label Specification) 解析为 PRISM 系统可用的 Bronze Layer 和 Meta 信息。

---

## 核心设计决策

### Bronze Layer: 按原始 Form 存储

- **不合并为 3 张表**，而是保留原始 form 结构
- 每个 form 一张表：`bronze.ae`, `bronze.cm`, `bronze.dm`, ...
- **优点**：完整的 traceability，结构简单

### 数据处理规则

1. **列名**：全部小写
2. **日期转换**：SAS date → DATE type
3. **不做数据筛选**：默认保留所有字段
4. **可选**：用户可指定删除不需要的列

---

## Meta 层结构

```
meta.study_info           -- Study 基本信息
meta.visits               -- Visit 定义
meta.form_classification  -- form → schema 分类
meta.bronze_dictionary    -- 所有 Bronze 变量（一张表，每变量一行）
meta.params               -- Longitudinal 参数（来自 Spec）
meta.attrs                -- Occurrence 扩展字段（来自 Spec）
meta.silver_dictionary    -- Silver 层数据字典（来自 Spec）
meta.gold_dictionary      -- Gold 层数据字典（来自 Spec）
meta.platinum_dictionary  -- Platinum 交付物定义（来自 Spec）
meta.dependencies         -- 变量依赖关系
```

---

## ALS Parser 输出

### 1. Bronze Tables（N 张）

按原始 form 生成，每个 form 一张表：

```sql
bronze.ae (
    usubjid TEXT NOT NULL,
    subjid TEXT,
    aeterm TEXT,
    aestdtc DATE,
    aeendtc DATE,
    aesoc TEXT,
    aedecod TEXT,
    ... (所有 AE 字段)
)

bronze.dm (
    usubjid TEXT NOT NULL,
    subjid TEXT,
    age INTEGER,
    sex TEXT,
    race TEXT,
    ... (所有 DM 字段)
)
```

### 2. Meta Tables

| 表 | 来源 |
|---|------|
| `meta.study_info` | ALS CRFDraft |
| `meta.visits` | ALS Folders |
| `meta.form_classification` | ALS Forms + 分类逻辑 |
| `meta.bronze_dictionary` | ALS Fields |

---

## Form 分类逻辑

```python
# Occurrence: 匹配 domain pattern
AE, AE1, AE2 → occurrence (domain=AE)
CM, CM1, CM2 → occurrence (domain=CM)
MH, MH1, MH2 → occurrence (domain=MH)

# Baseline: 只在 SCR/BASE folder 出现
DM, IC → baseline

# Longitudinal: 在多个 visit 出现
LB, VS, PK → longitudinal
```

---

## 文件清单

| 文件 | 说明 |
|------|------|
| `src/prism/sql/init_bronze.sql` | Bronze schema 说明（动态生成） |
| `src/prism/sql/init_meta.sql` | Meta schema DDL（10 张表） |
| `src/prism/meta/als_parser.py` | ALS 解析主逻辑 |
| `src/prism/meta/manager.py` | Meta 表操作方法 |

---

## 完成 ✓

- [x] 确认 Bronze 按原始 form 存储
- [x] 更新 `init_bronze.sql`
- [x] 更新 `als_parser.py`（生成 N 张 bronze 表）
- [x] 更新 `manager.py`（修复 add_bronze_variable）
- [x] 更新 `schema.py`（BronzeVariable 结构）
- [x] 测试通过（11 tests）

---

## 下一步

1. **Spec Parser**：解析 Spec 文件，填充 meta.params, meta.silver_dictionary, etc.
2. **Raw Data Loader**：加载 SAS/CSV 数据到 Bronze 表
3. **Silver Generator**：根据 Spec 生成 Silver 层
