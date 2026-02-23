# Working Log

## 2026-02-17

### Discussed
- Meta schema 重构：gold_dictionary.element_id 命名确认
- Gold 层设计：一行 = group + element + selection + statistics(JSON)
- platinum_dictionary.elements 结构确认：type + id + label/filter
- bronze/silver/gold 各层与 platinum 的关系

### Decisions
- `gold_dictionary.var_id` → `element_id` (统计对象：variable/param/coding_high/coding_low)
- `gold_dictionary.group_id` 是分组值（Drug, Placebo），不是分组变量名（TRTA）
- Gold 表用 JSON 存 statistics，而非每个 stat 一行
- `platinum_dictionary` 移除 `render_function`, `render_options`
- `platinum_dictionary.elements` 格式：`[{"type": "variable|param|attr", "id": "age", "label": "Age"}]`

### Completed
- 更新 `init_meta.sql` (v5.0 → v5.1)
- 更新 `init_gold.sql` (v3.1 → v4.0)
- 更新 `ARCHITECTURE.md` (Gold/Platinum 设计描述)
- 更新 `AGENTS.md` (Meta Schema 表列表)
- 更新 `CHANGELOG.md`
- 创建 `WORKING_LOG.md`

### Meta Schema v5.1 (10 Tables)

| Table | Purpose |
|-------|---------|
| `meta.study_info` | Study基本信息 |
| `meta.params` | Longitudinal参数定义 |
| `meta.attrs` | Occurrence domain扩展字段定义 |
| `meta.visits` | Analysis Visit定义 |
| `meta.bronze_dictionary` | Bronze层数据字典 |
| `meta.silver_dictionary` | Silver层数据字典 |
| `meta.form_classification` | Form → Domain/Schema 映射 |
| `meta.gold_dictionary` | Gold层统计定义 |
| `meta.platinum_dictionary` | Platinum交付物定义 |
| `meta.dependencies` | 变量依赖关系 |

---

## 2026-02-16

### Discussed
- Meta schema 整体重构方向
- Bronze/Silver/Gold/Platinum 各层职责
- ALS Parser 设计目标

### Decisions
- 变量表统一命名 `*_dictionary`
- `meta.flags` 重命名为 `meta.attrs`
- 删除 `meta.functions`（走 text-to-sql 路线）
- `meta.derivations` 合并到 `meta.silver_dictionary`
- `meta.outputs` 系列合并为 `meta.platinum_dictionary`

### Completed
- 重新设计 Meta Schema (v5.0)
- 更新 `init_meta.sql`
- 更新 `ARCHITECTURE.md`
- 更新 `AGENTS.md`
