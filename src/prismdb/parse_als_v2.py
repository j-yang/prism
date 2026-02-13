"""
ALS (EDC Schema) Parser v3.0
解析Medidata Rave ALS文件并自动填充DuckDB metadata

Changes from v2.0:
- 使用新的11张meta表
- 移除schema_docs，统一使用meta.variables
- add_variable签名已更新
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
import logging

from .database import Database
from .metadata import MetadataManager
from .classify_forms_v2 import classify_forms

logger = logging.getLogger(__name__)


def parse_als_to_db(
    als_path: str, db: Database, study_code: str = ""
) -> Dict[str, Any]:
    """
    解析ALS文件并填充到DuckDB

    Args:
        als_path: ALS文件路径
        db: Database实例
        study_code: 研究代码

    Returns:
        包含解析结果和统计信息的字典
    """
    logger.info(f"Parsing ALS: {als_path}")
    als_path = Path(als_path)

    # 1. 解析ALS文件
    als_data = _parse_als_file(als_path)

    # 2. 分类forms
    form_classification = classify_forms(
        forms=als_data["forms"],
        fields=als_data["fields"],
        matrices=als_data["matrices"],
        matrix_details=als_data["matrix_details"],
    )

    # 3. 生成Bronze DDL
    ddl_statements = _generate_bronze_ddl(als_data, form_classification)

    # 4. 创建Bronze表
    db.create_schema("bronze")
    for form_oid, ddl in ddl_statements.items():
        logger.info(f"Creating Bronze table: bronze.{form_oid.lower()}")
        db.execute(ddl)

    # 5. 设置study_info
    meta = MetadataManager(db)
    meta.set_study_info(study_code=study_code)

    # 6. 填充variables (替代旧的schema_docs + data_catalog)
    _populate_variables(meta, als_data, form_classification)

    # 7. 返回统计信息
    result = {
        "study_code": study_code,
        "forms_total": len(als_data["forms"]),
        "forms_by_type": {
            "baseline": len(form_classification["baseline"]),
            "longitudinal": len(form_classification["longitudinal"]),
            "occurrence": len(form_classification["occurrence"]),
        },
        "fields_total": len(als_data["fields"]),
        "codelists_total": len(als_data["codelists"]),
        "bronze_tables_created": len(ddl_statements),
        "classification": form_classification,
    }

    logger.info(
        f"ALS parsing complete: {result['forms_total']} forms, "
        f"{result['fields_total']} fields, "
        f"{result['bronze_tables_created']} Bronze tables"
    )

    return result


def _parse_als_file(als_path: Path) -> Dict[str, Any]:
    """解析ALS文件，返回结构化数据"""
    forms_df = pd.read_excel(als_path, sheet_name="Forms")
    fields_df = pd.read_excel(als_path, sheet_name="Fields")
    matrices_df = pd.read_excel(als_path, sheet_name="Matrices")

    codelists = _parse_codelists(als_path)

    xl = pd.ExcelFile(als_path)
    matrix_sheets = [s for s in xl.sheet_names if s.startswith("Matrix") and "#" in s]
    matrix_details = {}
    for sheet in matrix_sheets:
        matrix_details[sheet] = pd.read_excel(als_path, sheet_name=sheet)

    forms = []
    for _, row in forms_df.iterrows():
        forms.append(
            {
                "oid": row["OID"],
                "name": row["DraftFormName"],
                "active": row["DraftFormActive"],
            }
        )

    fields = []
    for _, row in fields_df.iterrows():
        field = {
            "form_oid": row["FormOID"],
            "field_oid": row["FieldOID"],
            "variable_oid": row["VariableOID"],
            "data_format": row["DataFormat"],
            "label": row["SASLabel"] if pd.notna(row["SASLabel"]) else row["FieldOID"],
            "codelist_name": row["DataDictionaryName"]
            if pd.notna(row["DataDictionaryName"])
            else None,
        }
        if field["codelist_name"] and field["codelist_name"] in codelists:
            field["codelist"] = codelists[field["codelist_name"]]
        fields.append(field)

    matrices = []
    for _, row in matrices_df.iterrows():
        matrices.append(
            {"oid": row["OID"], "name": row["MatrixName"], "addable": row["Addable"]}
        )

    return {
        "forms": forms,
        "fields": fields,
        "matrices": matrices,
        "matrix_details": matrix_details,
        "codelists": codelists,
    }


def _parse_codelists(als_path: Path) -> Dict[str, Dict[str, str]]:
    """解析DataDictionaries和DataDictionaryEntries"""
    try:
        dict_df = pd.read_excel(als_path, sheet_name="DataDictionaries")
        entries_df = pd.read_excel(als_path, sheet_name="DataDictionaryEntries")
    except Exception:
        return {}

    codelists = {}
    for _, row in dict_df.iterrows():
        dict_name = row["Name"] if "Name" in dict_df.columns else row.get("OID", "")
        codelists[dict_name] = {}

    for _, row in entries_df.iterrows():
        dict_name = row.get("DataDictionaryName", row.get("DataDictionaryOID", ""))
        if dict_name in codelists:
            coded = str(row.get("CodedData", row.get("CodedValue", "")))
            decode = str(row.get("UserDataString", row.get("Decode", "")))
            codelists[dict_name][coded] = decode

    return codelists


def _generate_bronze_ddl(als_data: Dict, form_classification: Dict) -> Dict[str, str]:
    """
    生成Bronze层DDL语句

    Returns:
        {form_oid: ddl_statement}
    """
    ddl_statements = {}

    fields_by_form = {}
    for field in als_data["fields"]:
        form_oid = field["form_oid"]
        if form_oid not in fields_by_form:
            fields_by_form[form_oid] = []
        fields_by_form[form_oid].append(field)

    for form in als_data["forms"]:
        form_oid = form["oid"]
        table_name = form_oid.lower()

        if form_oid not in fields_by_form:
            continue

        columns = [
            "    usubjid TEXT NOT NULL",
            "    folder_oid TEXT",
            "    folder_instance_id INTEGER",
            "    record_date DATE",
        ]

        added_columns = set()
        for field in fields_by_form[form_oid]:
            variable_oid = field.get("variable_oid")
            if not variable_oid or (
                isinstance(variable_oid, float) and pd.isna(variable_oid)
            ):
                continue

            col_name = str(variable_oid).lower()

            if col_name in added_columns:
                logger.warning(
                    f"Duplicate column {col_name} in form {form_oid}, skipping"
                )
                continue

            col_type = _map_data_format(field["data_format"])
            columns.append(f"    {col_name} {col_type}")
            added_columns.add(col_name)

        columns_str = ",\n".join(columns)
        ddl = f"""
CREATE TABLE IF NOT EXISTS bronze.{table_name} (
{columns_str},
    PRIMARY KEY (usubjid, folder_oid, folder_instance_id, record_date)
);
"""
        ddl_statements[form_oid] = ddl

    return ddl_statements


def _map_data_format(data_format: str) -> str:
    """映射ALS数据类型到DuckDB类型"""
    data_format = str(data_format).upper()

    if "TEXT" in data_format or "CHAR" in data_format:
        return "TEXT"
    elif "DATE" in data_format:
        return "DATE"
    elif "TIME" in data_format:
        return "TIMESTAMP"
    elif "INTEGER" in data_format or "INT" in data_format:
        return "INTEGER"
    elif "FLOAT" in data_format or "DOUBLE" in data_format:
        return "DOUBLE"
    else:
        return "TEXT"


def _populate_variables(
    meta: MetadataManager, als_data: Dict, form_classification: Dict
):
    """
    填充meta.variables表

    新设计：所有变量（包括Bronze层的原始列）都注册到meta.variables
    """
    logger.info("Populating meta.variables...")

    added_vars = set()

    for form in als_data["forms"]:
        form_oid = form["oid"]

        schema = None
        if form_oid in form_classification["baseline"]:
            schema = "baseline"
        elif form_oid in form_classification["longitudinal"]:
            schema = "longitudinal"
        elif form_oid in form_classification["occurrence"]:
            schema = "occurrence"
        else:
            continue

        for field in als_data["fields"]:
            if field["form_oid"] != form_oid:
                continue

            variable_oid = field.get("variable_oid")
            if not variable_oid or (
                isinstance(variable_oid, float) and pd.isna(variable_oid)
            ):
                continue

            var_name = str(variable_oid).lower()
            var_id = f"{form_oid.lower()}_{var_name}"

            if var_id in added_vars:
                continue

            data_type = _map_data_format(field["data_format"])

            # 对于longitudinal字段，可能是参数引用
            param_ref = None
            if schema == "longitudinal" and var_name.upper().startswith("PARAM"):
                param_ref = var_name.upper()

            meta.add_variable(
                var_id=var_id,
                var_name=var_name,
                schema=schema,
                var_label=field["label"],
                block=form_oid.upper(),
                data_type=data_type,
                param_ref=param_ref,
                flag_ref=None,
                is_baseline_of_param=False,
                display_order=None,
            )
            added_vars.add(var_id)

    logger.info(f"Variables populated: {len(added_vars)} records")


def parse_als(als_path: str) -> Dict[str, Any]:
    """
    (Legacy) 解析ALS文件，返回字典
    新代码请使用parse_als_to_db()
    """
    return _parse_als_file(Path(als_path))
