import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

from prism.core.database import Database
from prism.agent.llm import call_deepseek, extract_code_block

logger = logging.getLogger(__name__)


class SilverGenerator:
    TEMPLATES = {
        "date_min": {
            "pattern": r"(MIN\s*\(|earliest|first).*?(date|dtc|dtc)",
            "template": """-- [{deriv_id}] {target_var} (template: date_min)
SELECT usubjid, MIN({source_col}) AS {target_var}
FROM {source_table}
WHERE {condition}
GROUP BY usubjid;""",
        },
        "flag_case": {
            "pattern": r"(CASE\s*WHEN|flag|Y/N|THEN.*Y.*ELSE.*N)",
            "template": """-- [{deriv_id}] {target_var} (template: flag_case)
UPDATE silver.{schema}
SET {target_var} = CASE WHEN {condition} THEN 'Y' ELSE 'N' END;""",
        },
        "age_group": {
            "pattern": r"(age.*group|agegrp|agecat|\d+-\d+|>=65)",
            "template": """-- [{deriv_id}] {target_var} (template: age_group)
ALTER TABLE silver.{schema} ADD COLUMN IF NOT EXISTS {target_var} TEXT;
UPDATE silver.{schema}
SET {target_var} = CASE 
    WHEN {source_col} < 18 THEN '<18'
    WHEN {source_col} < 65 THEN '18-64'
    ELSE '>=65'
END;""",
        },
        "direct_copy": {
            "pattern": r"(Take|Equal to|copy|direct|取)",
            "template": """-- [{deriv_id}] {target_var} (template: direct_copy)
SELECT usubjid, {source_col} AS {target_var}
FROM {source_table}
WHERE {condition};""",
        },
        "concat": {
            "pattern": r"(concat|Concatenate|\|\|)",
            "template": """-- [{deriv_id}] {target_var} (template: concat)
SELECT usubjid, {source_cols} AS {target_var}
FROM {source_table}
WHERE {condition};""",
        },
        "change_baseline": {
            "pattern": r"(change|chg|baseline|BASE|AVAL.*\-)",
            "template": """-- [{deriv_id}] {target_var} (template: change_baseline)
SELECT 
    usubjid, 
    paramcd, 
    visitnum,
    aval,
    FIRST_VALUE(aval) OVER (PARTITION BY usubjid, paramcd ORDER BY visitnum) AS base,
    aval - FIRST_VALUE(aval) OVER (PARTITION BY usubjid, paramcd ORDER BY visitnum) AS {target_var}
FROM {source_table}
WHERE paramcd IS NOT NULL;""",
        },
    }

    def __init__(self, db: Database, api_key: str = None):
        self.db = db
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        self.generation_log = {
            "generated_at": None,
            "stats": {"total": 0, "template": 0, "llm": 0, "skipped": 0},
            "derivations": [],
        }

    def generate_all(self, output_dir: str = "generated/") -> Dict[str, Any]:
        os.makedirs(output_dir, exist_ok=True)
        self.generation_log["generated_at"] = datetime.now().isoformat()

        derivations = self._load_derivations()
        bronze_schema = self._get_bronze_schema()

        for schema in ["baseline", "occurrence", "longitudinal"]:
            schema_derivs = derivations.get(schema, [])
            if not schema_derivs:
                continue

            sql_parts = [self._file_header(schema)]

            for deriv in schema_derivs:
                sql = self._generate_single(deriv, bronze_schema)
                if sql:
                    sql_parts.append(sql)

            output_file = os.path.join(output_dir, f"derive_{schema}.sql")
            self._write_file(output_file, "\n\n".join(sql_parts))
            logger.info(f"Generated: {output_file}")

        log_file = os.path.join(output_dir, "generation_log.json")
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(self.generation_log, f, indent=2, ensure_ascii=False)

        return self.generation_log

    def _load_derivations(self) -> Dict[str, List[Dict]]:
        sql = """
            SELECT d.*, v.schema, v.var_name, v.var_label, v.data_type
            FROM meta.derivations d
            JOIN meta.variables v ON d.target_var = v.var_id
            ORDER BY v.schema, d.deriv_id
        """
        df = self.db.query_df(sql)

        result = {"baseline": [], "occurrence": [], "longitudinal": []}
        for _, row in df.iterrows():
            schema = row["schema"]
            if schema in result:
                result[schema].append(row.to_dict())

        return result

    def _get_bronze_schema(self) -> Dict[str, List[Dict]]:
        bronze_tables = self.db.list_tables("bronze")
        schema_info = {}

        for table in bronze_tables:
            cols = self.db.query_df(f"DESCRIBE bronze.{table}")
            schema_info[table] = [
                {"name": row["column_name"], "type": row["column_type"]}
                for _, row in cols.iterrows()
            ]

        return schema_info

    def _generate_single(self, deriv: Dict, bronze_schema: Dict) -> Optional[str]:
        deriv_id = deriv["deriv_id"]
        target_var = deriv["target_var"]
        transformation = deriv.get("transformation", "")
        complexity = deriv.get("complexity", "medium")
        schema = deriv["schema"]

        log_entry = {
            "deriv_id": deriv_id,
            "target_var": target_var,
            "schema": schema,
            "complexity": complexity,
            "method": None,
            "confidence": 0.0,
            "needs_review": False,
            "status": "success",
        }

        self.generation_log["stats"]["total"] += 1

        sql = self._try_template(deriv)
        if sql:
            log_entry["method"] = "template"
            log_entry["confidence"] = 1.0
            self.generation_log["stats"]["template"] += 1
        else:
            sql = self._call_llm(deriv, bronze_schema)
            if sql:
                log_entry["method"] = "llm"
                log_entry["confidence"] = 0.7
                log_entry["needs_review"] = True
                self.generation_log["stats"]["llm"] += 1
            else:
                log_entry["status"] = "skipped"
                log_entry["needs_review"] = True
                self.generation_log["stats"]["skipped"] += 1
                sql = self._placeholder_sql(deriv)

        self.generation_log["derivations"].append(log_entry)
        return sql

    def _try_template(self, deriv: Dict) -> Optional[str]:
        transformation = deriv.get("transformation", "")
        if not transformation:
            return None

        for template_name, template_info in self.TEMPLATES.items():
            pattern = template_info["pattern"]
            if re.search(pattern, transformation, re.IGNORECASE):
                return self._render_template(template_info["template"], deriv)

        return None

    def _render_template(self, template: str, deriv: Dict) -> str:
        source_vars = deriv.get("source_vars", [])
        source_tables = deriv.get("source_tables", [])

        if source_vars is None or (
            isinstance(source_vars, float) and pd.isna(source_vars)
        ):
            source_vars = "[]"
        if source_tables is None or (
            isinstance(source_tables, float) and pd.isna(source_tables)
        ):
            source_tables = "[]"

        source_vars_list = (
            json.loads(source_vars)
            if isinstance(source_vars, str)
            else (source_vars or [])
        )
        source_tables_list = (
            json.loads(source_tables)
            if isinstance(source_tables, str)
            else (source_tables or [])
        )

        source_col = source_vars_list[0] if source_vars_list else "unknown_col"
        source_table = source_tables_list[0] if source_tables_list else "bronze.unknown"
        if not source_table.startswith("bronze."):
            source_table = f"bronze.{source_table}"

        return template.format(
            deriv_id=deriv["deriv_id"],
            target_var=deriv["target_var"],
            schema=deriv["schema"],
            source_col=source_col,
            source_cols=", ".join(source_vars_list) if source_vars_list else source_col,
            source_table=source_table,
            condition="1=1",
        )

    def _call_llm(self, deriv: Dict, bronze_schema: Dict) -> Optional[str]:
        if not self.api_key:
            logger.warning(f"No DEEPSEEK_API_KEY, skipping LLM for {deriv['deriv_id']}")
            return None

        prompt = self._build_prompt(deriv, bronze_schema)
        content = call_deepseek(prompt)

        if content:
            return self._extract_sql(content, deriv)
        return None

    def _build_prompt(self, deriv: Dict, bronze_schema: Dict) -> str:
        target_var = deriv["target_var"]
        schema = deriv["schema"]
        transformation = deriv.get("transformation", "")
        var_label = deriv.get("var_label", "")
        data_type = deriv.get("data_type", "")

        source_vars = deriv.get("source_vars", [])
        source_tables = deriv.get("source_tables", [])
        source_vars_list = (
            json.loads(source_vars)
            if isinstance(source_vars, str)
            else (source_vars or [])
        )
        source_tables_list = (
            json.loads(source_tables)
            if isinstance(source_tables, str)
            else (source_tables or [])
        )

        schema_info = ""
        for table in source_tables_list[:3]:
            table_name = (
                table.replace("bronze.", "") if table.startswith("bronze.") else table
            )
            if table_name in bronze_schema:
                cols = bronze_schema[table_name]
                schema_info += f"\nbronze.{table_name}:\n"
                for col in cols[:10]:
                    schema_info += f"  - {col['name']}: {col['type']}\n"

        return f"""你是一个临床试验数据处理的SQL专家。

## 任务
根据以下衍生规则生成DuckDB SQL。

## 目标变量
- 变量名: {target_var}
- Schema: {schema}
- 标签: {var_label}
- 数据类型: {data_type}

## 衍生规则
{transformation}

## 源变量
{", ".join(source_vars_list) if source_vars_list else "未指定"}

## 源表结构
{schema_info if schema_info else "未指定"}

## 要求
1. 只输出SQL代码，不要解释
2. 使用DuckDB语法
3. 主键是usubjid
4. 输出INSERT或UPDATE语句
5. 添加注释说明目标变量

## SQL
```sql"""

    def _extract_sql(self, content: str, deriv: Dict) -> str:
        sql = extract_code_block(content, "sql")

        header = f"""-- [{deriv["deriv_id"]}] {deriv["target_var"]} (method: llm)
-- Complexity: {deriv.get("complexity", "medium")}
-- NEEDS REVIEW: LLM generated, please verify
-- Rule: {deriv.get("transformation", "")[:100]}..."""

        return f"{header}\n{sql}"

    def _placeholder_sql(self, deriv: Dict) -> str:
        return f"""-- [{deriv["deriv_id"]}] {deriv["target_var"]} (SKIPPED)
-- MANUAL INTERVENTION REQUIRED
-- Complexity: {deriv.get("complexity", "unknown")}
-- Rule: {deriv.get("transformation", "No rule defined")}
-- TODO: Write SQL for this derivation
-- INSERT INTO silver.{deriv["schema"]} (...) VALUES (...);"""

    def _file_header(self, schema: str) -> str:
        return f"""-- ============================================================================
-- PRISM Silver Layer Derivation Script
-- Schema: {schema}
-- Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
-- ============================================================================

-- Ensure silver schema exists
CREATE SCHEMA IF NOT EXISTS silver;

-- Create base table if not exists
CREATE TABLE IF NOT EXISTS silver.{schema} (
    usubjid TEXT PRIMARY KEY
);

"""

    def _write_file(self, filepath: str, content: str) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)


import pandas as pd
