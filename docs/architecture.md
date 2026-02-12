# Prism-Agent Architecture (Spec + Param Recipes → R Code)

> 目标：让 AI 在“少数复杂规则（尤其 BDS 参数 AVAL）”上发挥能力，同时保证整体流程可复现、可审计、可维护。
>
> 核心决定：
> - 多个 study 共享一个 Excel（side-by-side 宽表），共享 `FUNCTION_POOL` 与 `PARAM_POOL`。
> - Excel 只是编辑界面；生成时先归一化为每个 study 一份结构化 Spec（YAML/JSON）。
> - `PARAM_POOL` + `param_recipe`（版本化 DSL）入库沉淀复用；普通变量尽量用函数库“一步得出”，不需要 AI。
> - AI 主要负责把 raw 自然语言描述整理成**结构化 recipe DSL**，再由编译器确定性生成 R。

---

## 1. 关键概念（名词解释）

### 1.1 Spec（Study Mapping Spec）
- **定义**：描述“某个 study 要生成哪些 ADaM dataset/变量/参数，以及如何派生”的结构化输入。
- **来源**：由 Excel（宽表）导出为每个 study 的 `study.yaml` 或 `study.json`。
- **目的**：作为代码生成的权威输入（source of truth），可在 Git 中做 diff、review、版本化。

### 1.2 Function Catalog（函数合同/白名单）
- **定义**：对 R 函数库的机器可读说明（函数名、签名、参数类型/默认值、输出、约束、示例）。
- **意义**：
  - 防止 AI 乱编函数名/参数。
  - 生成器可做静态校验：函数是否存在、参数是否齐全、类型是否匹配。

### 1.3 Param Pool（参数池）
- **定义**：BDS 型 ADaM（如 ADLB）中参数的标准字典，至少包含 `PARAM/PARAMCD/AVALU`，以及必要的默认规则元数据。
- **特点**：跨 study 可复用，适合入库沉淀。

### 1.4 Recipe（配方）
- **定义**：描述复杂派生逻辑的一份“可复用、可版本化”的规则（通常针对某个 `PARAMCD` 的 `AVAL` 派生）。
- **特点**：跨 study 复用（默认一致）；允许 per-study override（窗口/基线/过滤条件等）。

### 1.5 DSL（Domain-Specific Language，领域专用语言）
- **定义**：用 JSON/YAML 表达的**受限、结构化**规则语言，用来表示 recipe。
- **为什么要 DSL（而不是直接让 AI 写自由 R）**：
  - 可校验：字段依赖、函数签名、单位换算可用性、禁止不安全操作。
  - 可编译：DSL → R 代码由编译器确定性生成，输出风格一致。
  - 可审计：每个输出能追溯到 recipe_id/version + spec version。

---

## 2. 当前 Excel 模板的观测（用于落地解析器）

已从 Excel 抽取到的 sheet + headers（见 `excel_schema.json`）：
- `Studies`: `Study Code`, ...
- `FUNCTION_POOL`: `FUNCTION_NAME`, `FUNCTIONALITY`
- `PARAM_POOL`: `PARAM`, `PARAMCD`, `AVALU`, `AVAL`, `DOAMIN`
- Dataset sheets（示例 `ADSL/ADBASE/ADLB`）：`Variable Name`, `Variable Label`, `Type`, `<StudyIdColumn>`（例如 `D8318N00001`）

说明：dataset sheet 采用“宽表”：每个 study 一列规则。这个不会影响流程，只要求在导出 spec 时做归一化（宽→长）。

---

## 3. 总体架构（End-to-End Picture）

### 3.1 数据流
1) Excel（多个 study side-by-side）
→ 2) 解析/导出：每个 study 生成一份 Spec（YAML/JSON）
→ 3) Resolver：Spec + Param/Function 库（DB/文件）合并成 IR（中间表示）
→ 4) Compiler：
   - 简单变量：按 `copy/function/expr/constant` 模板生成 R
   - BDS 参数：按 `param_recipe DSL` 编译生成 R
→ 5) Assembler：组装成每个 dataset 一个 R 脚本 + manifest
→ 6)（可选）执行与验证：跑小样本/回归测试，输出报告

### 3.2 组件划分
- **Spec Exporter（Excel → Spec）**：确定性，不需要 AI。
- **Library Store（Param/Recipe DB + Function catalog）**：权威资产库。
- **AI Recipe Authoring（raw text → DSL）**：AI 参与点。
- **Codegen/Compiler（DSL/Spec → R）**：确定性，风格统一。
- **Validator（静态/可选运行）**：质量闸门。

---

## 4. 分步实施计划（步骤 + 技术框架）

> 下面按“最小可行（MVP）→可扩展”的顺序。

### Step 0 — 约定与规范（必须先做）
**产物**
- Excel 约定：study 列如何识别、空单元格语义（不适用 vs 继承默认）、规则语法最小集合。
- Spec 的 JSON Schema（对外契约）。

**技术要点/框架**
- JSON Schema：`jsonschema`
- Python 结构化模型：`pydantic`

---

### Step 1 — Excel → Spec（宽表归一化导出）
**要解决的问题**
- 多 study 同一张表：`ADLB` sheet 的 `D8318N00001` 等列需要按 `study_id` 参数选择。
- 导出后一律变成“每个 study 一份 spec”，后续系统不再感知 Excel 是宽表。

**建议的导出策略**
- CLI 参数：`--study-id D8318N00001`
- 解析器规则：
  - dataset sheet：固定列（Variable Name/Label/Type）+ N 个 study 列
  - 选择 study 列抽取 derivation 单元格内容
  - 空值语义：建议支持两种模式（可配置）
    - `empty_means: not_applicable`
    - `empty_means: inherit_default`（建议配一个 `DEFAULT` 列）

**技术框架**
- 读 Excel：`openpyxl`
- CLI：`typer`
- 输出 YAML：`ruamel.yaml` 或 `PyYAML`
- 校验：`pydantic` + `jsonschema`

---

### Step 2 — Function Catalog（函数合同）
**要解决的问题**
- 简单变量派生要做到“AI 不参与也能稳定生成”。
- AI 也只能调用白名单函数。

**产物**
- `function_catalog.json`（或从 R package 文档生成）
- R 函数库建议做成独立 R package（便于版本与测试）

**技术框架**
- Catalog 生成/维护：Python（`pydantic`）或直接手写 JSON/YAML
- R package：`roxygen2`, `testthat`, `lintr`

---

### Step 3 — Param Pool + Recipe DB（仅沉淀可复用资产）
**核心决定**
- 普通变量规则不入库（study-specific，变动频繁），走 spec。
- 复杂逻辑主要集中在 BDS 的 param AVAL：param/recipe 入库并版本化。

**建议 DB 表（最小集）**
- `param`：`dataset`, `PARAMCD`, `PARAM`, `default_unit`(AVALU), `metadata_json`
- `param_recipe`：`recipe_id`, `version`, `dsl_json`, `status`(draft/approved), `hash`, `created_at`, `supersedes`
- `param_binding`：`study_id`, `dataset`, `PARAMCD`, `recipe_id`, `version_pin?`, `override_json`
- `function`（可选）：将 catalog 同步进 DB 便于查询/治理
- `recipe_example`（可选）：历史生成代码片段/评审说明/失败用例（支持检索复用）

**技术框架**
- DB：MVP 用 SQLite；团队共享用 Postgres
- ORM + 迁移：`SQLAlchemy` + `Alembic`
- （可选）向量检索：Postgres + `pgvector` 或本地 `faiss`

---

### Step 4 — Recipe DSL（结构化配方语言）与编译器
**DSL 推荐形态**
- JSON/YAML，严格 schema。
- 包含：
  - `inputs`: 依赖的源表/列
  - `steps[]`: 有序步骤（每步一个 primitive）
  - `outputs`: 产出变量（如 AVAL/AVALC/DTYPE）
  - `checks`: 规则级断言（类型/单位/范围/非空等）

**为什么必须先 DSL 再 R**
- 让 AI 输出“可验证的结构化计划”，再编译成 R。

**技术框架**
- DSL schema：`pydantic` + `jsonschema`
- 编译：Python 自研 compiler（+ `jinja2` 统一模板/代码风格）
- R 目标栈：固定 `dplyr` 或 `data.table`（建议只选一种）

---

### Step 5 — AI 参与点（只处理复杂 recipe 的长尾）
**AI 做什么**
- 将 raw 自然语言 derivation 描述 → 结构化 DSL（Stage A）。
- （可选）基于 DSL 生成 R 代码片段解释/注释（Stage B），最终仍以编译器产物为准。

**AI 不做什么**
- 不允许 AI 猜 PARAMCD/unit。
- 不允许 AI 引入 catalog 外函数。
- 不允许 AI 输出“未经校验就进入主干”的自由 R。

**技术框架（LLM）**
- LLM SDK：Azure OpenAI 或 OpenAI SDK；或用 `litellm` 做多模型适配
- 编排（可选）：`langgraph`（多步、带状态）或轻量自研（规则强时更稳）
- 检索（可选）：对 `recipe_example`、已批准 recipe、函数文档做相似检索（pgvector/faiss）

---

### Step 6 — 验证、回归与发布
**最小验证（不执行 R 也要做）**
- Spec/DSL schema 校验
- 函数签名校验（catalog）
- 字段依赖校验（引用列是否声明/存在）
- 循环依赖检测（变量/步骤依赖图）

**可选：执行验证（强烈推荐用于 recipe）**
- 小样本/fixtures：对关键 param recipe 跑 test
- 回归对比：与历史 study 或金标准输出对比

**技术框架**
- Python：`pytest`
- R：`testthat`
- 环境锁定（可选）：`renv` + Docker

---

## 5. 目录结构建议（Python package）

建议以 Python package 方式组织（MVP 不需要 MCP server）：

- `src/prism_codegen/`
  - `excel/`（读 Excel → spec）
  - `spec/`（pydantic models + schema）
  - `catalog/`（function catalog 读写与校验）
  - `db/`（SQLAlchemy models + repositories + migrations）
  - `dsl/`（recipe DSL models + validators）
  - `compiler/`（DSL/spec → IR → R code）
  - `ai/`（LLM 调用、prompt、检索、recipe authoring）
  - `cli.py`（typer CLI）

---

## 6. MCP server 是否需要？（结论）

- **MVP 阶段不需要**：单项目/单团队内使用，Python library + CLI 最快。
- **需要时再加**：当你希望 VS Code/多个 agent/多个语言客户端共享“取 recipe/param、生成代码、查询资产库”能力时，再把关键能力封装成 API 或 MCP tools。

---

## 7. 下一步建议（从现在开始最有价值的 3 件事）

1) 明确空单元格语义 + 是否增加 `DEFAULT` 列（继承机制）。
2) 从 `PARAM_POOL` 选 2–3 个典型 PARAM（一个简单、一个复杂 AVAL、一个需要单位/窗口/基线），定义第一版 recipe DSL schema。
3) 固定 R 目标栈（`dplyr` or `data.table`）并写出 1 个 dataset（建议 ADLB）生成器的最小闭环。
