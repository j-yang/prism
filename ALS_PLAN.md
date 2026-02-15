# ALS Parser 改造计划

## 目标

将 ALS (Annotated Label Specification) 解析为 PRISM 系统可用的 Bronze Layer 和 Meta 信息。

## 核心输出

### Bronze Layer (3张表)

```sql
-- Baseline: 每个受试者一条记录
bronze.baseline (
  usubjid TEXT PRIMARY KEY,
  subjid TEXT,
  attrs JSON
)

-- Longitudinal: 每个受试者每个 visit 一条记录
bronze.longitudinal (
  usubjid TEXT,
  subjid TEXT,
  visit_id TEXT,
  attrs JSON,
  PRIMARY KEY (usubjid, visit_id)
)

-- Occurrence: 每个事件一条记录，合并多个 domain
bronze.occurrence (
  usubjid TEXT,
  subjid TEXT,
  domain TEXT,        -- AE/CM/MH/PR/DEATH
  seq INTEGER,
  term TEXT,
  startdt DATE,
  enddt DATE,
  coding_high TEXT,   -- SOC/ATC1 (placeholder)
  coding_low TEXT,    -- PT/Drug (placeholder)
  attrs JSON,
  PRIMARY KEY (usubjid, domain, seq)
)
```

### Meta Layer

```sql
meta.study_info        -- study 基本信息
meta.visits            -- visit 定义
meta.form_classification  -- form → domain/分类映射
```

---

## Domain 映射规则

```python
DOMAIN_MAPPING = {
    "AE": ["AE", "AE1", "AE2"],
    "CM": ["CM", "CM1", "CM2"],
    "MH": ["MH", "MH1", "MH2"],
    "PR": ["PR", "PR1", "PR2"],
    "DEATH": ["DS", "DS1", "DTH"],
}
```

## 字段映射 (Placeholder)

```python
DOMAIN_FIELD_MAPPING = {
    "AE": {
        "term": "AETERM",
        "startdt": "AESTDTC",
        "enddt": "AEENDTC",
        "coding_high": "AESOC",
        "coding_low": "AEDECOD",
    },
    "CM": {
        "term": "CMTRT",
        "startdt": "CMSTDTC",
        "enddt": "CMENDTC",
        "coding_high": "CMATC1",
        "coding_low": "CMDECOD",
    },
    "MH": {
        "term": "MHTERM",
        "startdt": "MHSTDTC",
        "enddt": "MHENDTC",
        "coding_high": "MHSOC",
        "coding_low": "MHDECOD",
    },
    # ...
}
```

---

## Form 分类逻辑

```
1. Occurrence: form_oid 匹配 DOMAIN_MAPPING 中的任意 pattern
2. Baseline:   只在 SCR/BASE folder 出现，且非 occurrence
3. Longitudinal: 多 visit 出现，且非 occurrence
4. Unknown:    无法判断，记录日志待人工确认
```

---

## TODO

- [x] 分析 ALS 结构，确认需求
- [x] 设计 Bronze 表结构
- [x] 设计 Meta 表结构
- [x] 重构 als_parser.py
  - [x] 实现 Domain 映射逻辑
  - [x] 实现字段映射配置
  - [x] 实现 Form 分类逻辑
  - [x] 生成 Bronze DDL
- [x] 创建/更新 init_meta.sql
  - [x] 添加 meta.form_classification 表
- [x] 创建 init_bronze.sql
- [x] 更新 manager.py
  - [x] 添加 add_form_classification 方法
  - [x] 添加 get_form_classification 方法
  - [x] 添加 get_forms_by_domain 方法
- [x] 测试用例
- [ ] 文档更新

---

## Progress

### 2025-02-16
- [x] 完成需求讨论和结构设计
- [x] 确认 Bronze 三张表结构
- [x] 确认 Domain 合并策略
- [x] 代码实现完成
- [x] 测试通过 (8 passed, 3 passed with ALS file)

---

## 文件清单

| 文件 | 状态 | 说明 |
|------|------|------|
| `src/prism/meta/als_parser.py` | ✅ 完成 | ALS 解析主逻辑 |
| `src/prism/meta/manager.py` | ✅ 完成 | 添加 form_classification 管理 |
| `src/prism/sql/init_meta.sql` | ✅ 完成 | 添加 form_classification 表 |
| `src/prism/sql/init_bronze.sql` | ✅ 完成 | Bronze 表 DDL |
| `tests/test_als_parser.py` | ✅ 完成 | 测试用例 |

---

## 下一步

1. **Spec Parser**: 解析 Spec 文件，填充 meta.params, meta.flags, meta.derivations, meta.outputs
2. **Raw Data Loader**: 加载 Raw SAS 数据到 Bronze 表
3. **Silver Generator**: 根据 Spec 生成 Silver 层
4. **Agent Integration**: 使用 LLM 生成复杂的 derivation SQL
