# Working Log

## 2026-02-24

### Discussed
- Spec Agent 设计：如何从 Mock Shell 自动生成 clinical trial spec
- Spec 文件格式：Excel vs DB，最终选择 Excel + DB 混合方案
- Agent 架构：LLM 为核心，Memory Store 用于跨 study 学习

### Decisions
- Spec Agent 放在 `prism/spec/` 模块
- Memory Store 用 DuckDB 存储在 `~/.prism/memory.duckdb`
- 变量命名使用 snake_case 描述性风格
- Excel Spec 包含 5 个 sheets：study_config, params, silver_variables, platinum, gold_statistics

### Completed
- 创建 `prism/spec/` 模块（8 个文件，~750 行代码）
  - `extractor.py` - Mock Shell 解析器（docx/xlsx）
  - `templates.py` - LLM Prompt 模板
  - `generator.py` - Spec 生成器
  - `matcher.py` - ALS 变量匹配
  - `learner.py` - Diff 学习器
  - `memory.py` - DuckDB 存储
  - `excel_writer.py` - 格式化 Excel 输出
  - `cli.py` - 命令行接口
- 创建 `prism/cli.py` 主入口
- 更新 `pyproject.toml` 添加 prism 命令和 python-docx 依赖
- 生成示例 spec：`examples/some_study/spec_full.xlsx`

### Spec Agent 架构

```
INPUT                    AGENT                    OUTPUT
┌─────────┐                                       
│Mock     │──┐                                      
│Shell    │  │     ┌─────────────────┐             
└─────────┘  │     │                 │    ┌───────┐
             ├────▶│   Spec Agent    │───▶│ Spec  │
┌─────────┐  │     │   (LLM-core)    │    │.xlsx  │
│  ALS    │──┘     │                 │    └───────┘
└─────────┘        └────────┬────────┘
                            │
                   ┌────────▼────────┐
                   │  Memory Store   │
                   │  (DuckDB file)  │
                   └─────────────────┘
```

### CLI Usage

```bash
# 生成 spec
prism spec generate --mock shell.docx --als als.xlsx --output spec.xlsx

# 查看 deliverables
prism spec generate --mock shell.docx --als als.xlsx --list-only

# 学习修正
prism spec learn --original draft.json --corrected final.json --study GC012F

# 查看 patterns
prism spec patterns stats
prism spec patterns list
```

### Excel Spec Layout

| Sheet | 内容 |
|-------|------|
| study_config | Populations, Event Periods |
| params | Longitudinal 参数定义 |
| silver_variables | 变量 + derivation |
| platinum | 交付物列表 |
| gold_statistics | 统计量定义 |
| review_needed | 需要 review 的项 |

---

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
