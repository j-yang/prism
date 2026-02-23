"""
ALS Parser for PRISM

Parses Annotated Label Specification (ALS) files and generates:
1. Bronze layer tables (one per form)
2. Meta tables (study_info, visits, form_classification, bronze_dictionary)
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
import json
import logging

from prism.core.database import Database
from prism.meta.manager import MetadataManager

logger = logging.getLogger(__name__)

DOMAIN_MAPPING: Dict[str, List[str]] = {
    "AE": ["AE", "AE1", "AE2", "AE3"],
    "CM": ["CM", "CM1", "CM2", "CM3"],
    "MH": ["MH", "MH1", "MH2", "MH3"],
    "PR": ["PR", "PR1", "PR2", "PR3"],
    "DEATH": ["DS", "DS1", "DTH", "DEATH"],
}

BASELINE_FOLDER_PATTERNS = ["SCR", "BASE", "SCREEN"]
FOLLOWUP_FOLDER_PATTERNS = ["SFU", "LFU", "EC", "COL"]


def get_domain_for_form(form_oid: str) -> Optional[str]:
    form_upper = form_oid.upper()
    for domain, patterns in DOMAIN_MAPPING.items():
        for pattern in patterns:
            if form_upper == pattern or form_upper.startswith(pattern):
                return domain
    return None


def classify_forms(
    forms: List[Dict],
    fields: List[Dict],
    matrices: Dict[str, List[str]],
) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}

    for form in forms:
        form_oid = form["oid"]
        form_name = form.get("name", "").lower()

        domain = get_domain_for_form(form_oid)

        if domain:
            result[form_oid] = {
                "domain": domain,
                "schema": "occurrence",
                "source_forms": [form_oid],
                "confidence": "high",
            }
            continue

        folders = matrices.get(form_oid, [])

        is_baseline_only = (
            all(
                any(pattern in f for pattern in BASELINE_FOLDER_PATTERNS)
                for f in folders
            )
            or len(folders) == 0
        )

        has_followup = any(
            any(pattern in f for pattern in FOLLOWUP_FOLDER_PATTERNS) for f in folders
        )

        is_log = any(
            f.get("form_oid") == form_oid and bool(f.get("is_log", False))
            for f in fields
        )

        if is_baseline_only and not has_followup:
            result[form_oid] = {
                "domain": None,
                "schema": "baseline",
                "source_forms": [form_oid],
                "confidence": "medium",
            }
        elif has_followup or is_log:
            result[form_oid] = {
                "domain": None,
                "schema": "longitudinal",
                "source_forms": [form_oid],
                "confidence": "medium",
            }
        else:
            result[form_oid] = {
                "domain": None,
                "schema": "unknown",
                "source_forms": [form_oid],
                "confidence": "low",
            }

    return result


def _parse_als_file(als_path: Path) -> Dict[str, Any]:
    xl = pd.ExcelFile(als_path)

    forms_df = pd.read_excel(xl, sheet_name="Forms")
    fields_df = pd.read_excel(xl, sheet_name="Fields")
    folders_df = pd.read_excel(xl, sheet_name="Folders")

    forms = []
    for _, row in forms_df.iterrows():
        forms.append(
            {
                "oid": str(row["OID"]),
                "name": str(row.get("DraftFormName", "")),
                "active": row.get("DraftFormActive", True),
            }
        )

    fields = []
    for _, row in fields_df.iterrows():
        fields.append(
            {
                "form_oid": str(row["FormOID"]),
                "field_oid": str(row["FieldOID"]),
                "variable_oid": str(row["VariableOID"])
                if pd.notna(row.get("VariableOID"))
                else None,
                "data_format": str(row.get("DataFormat", "")),
                "label": str(row["SASLabel"])
                if pd.notna(row.get("SASLabel"))
                else str(row["FieldOID"]),
                "is_log": row.get("IsLog", False),
                "codelist_name": str(row["DataDictionaryName"])
                if pd.notna(row.get("DataDictionaryName"))
                else None,
            }
        )

    folders = []
    for _, row in folders_df.iterrows():
        folders.append(
            {
                "oid": str(row["OID"]),
                "name": str(row["FolderName"]),
                "ordinal": row.get("Ordinal"),
            }
        )

    matrices = _parse_matrices(xl, forms)

    codelists = _parse_codelists(xl)

    crf_draft = pd.read_excel(xl, sheet_name="CRFDraft")

    return {
        "forms": forms,
        "fields": fields,
        "folders": folders,
        "matrices": matrices,
        "codelists": codelists,
        "crf_draft": crf_draft,
    }


def _parse_matrices(xl: pd.ExcelFile, forms: List[Dict]) -> Dict[str, List[str]]:
    matrices: Dict[str, List[str]] = {f["oid"]: [] for f in forms}

    matrix_sheets = [s for s in xl.sheet_names if s.startswith("Matrix") and "#" in s]

    for sheet in matrix_sheets:
        df = pd.read_excel(xl, sheet_name=sheet)
        folder_oid = sheet.split("#")[1] if "#" in sheet else sheet

        form_col = df.columns[0]
        for _, row in df.iterrows():
            form_oid = str(row[form_col])
            if form_oid in matrices:
                matrices[form_oid].append(folder_oid)

    return matrices


def _parse_codelists(xl: pd.ExcelFile) -> Dict[str, Dict[str, str]]:
    try:
        dict_df = pd.read_excel(xl, sheet_name="DataDictionaries")
        entries_df = pd.read_excel(xl, sheet_name="DataDictionaryEntries")
    except Exception:
        return {}

    codelists: Dict[str, Dict[str, str]] = {}
    for _, row in dict_df.iterrows():
        dict_name = str(row.get("DataDictionaryName", row.get("OID", "")))
        codelists[dict_name] = {}

    for _, row in entries_df.iterrows():
        dict_name = str(row.get("DataDictionaryName", row.get("DataDictionaryOID", "")))
        if dict_name in codelists:
            coded = str(row.get("CodedData", row.get("CodedValue", "")))
            decode = str(row.get("UserDataString", row.get("Decode", "")))
            codelists[dict_name][coded] = decode

    return codelists


def _infer_data_type(data_format: str) -> str:
    if not data_format:
        return "TEXT"

    fmt = str(data_format).upper()

    if "DATE" in fmt or "YYYY" in fmt:
        return "DATE"
    if "TIME" in fmt or "HH" in fmt:
        return "TIMESTAMP"

    try:
        if "." in data_format:
            return "DOUBLE"
        if data_format.isdigit():
            return "INTEGER"
    except Exception:
        pass

    if data_format.startswith("$"):
        return "TEXT"

    return "TEXT"


def generate_bronze_ddl(form_oid: str, fields: List[Dict]) -> str:
    form_fields = [f for f in fields if f["form_oid"] == form_oid]

    columns = ["    usubjid TEXT NOT NULL", "    subjid TEXT"]

    for field in form_fields:
        var_name = (field["variable_oid"] or field["field_oid"]).lower()
        data_type = _infer_data_type(field.get("data_format", ""))
        columns.append(f"    {var_name} {data_type}")

    ddl = f"""CREATE TABLE IF NOT EXISTS bronze.{form_oid.lower()} (
{",\n".join(columns)}
);

COMMENT ON TABLE bronze.{form_oid.lower()} IS 'Raw data from form {form_oid}';

"""
    return ddl


def parse_als_to_db(
    als_path: str,
    db: Database,
    study_code: str = "",
) -> Dict[str, Any]:
    logger.info(f"Parsing ALS: {als_path}")
    als_path_obj = Path(als_path)

    als_data = _parse_als_file(als_path_obj)

    form_classification = classify_forms(
        forms=als_data["forms"],
        fields=als_data["fields"],
        matrices=als_data["matrices"],
    )

    db.execute("CREATE SCHEMA IF NOT EXISTS bronze")

    meta = MetadataManager(db)

    crf_draft = als_data.get("crf_draft")
    als_version = None
    if crf_draft is not None and len(crf_draft) > 0:
        als_version = str(crf_draft.iloc[0].get("DraftName", ""))

    meta.set_study_info(
        studyid=study_code or "STUDY001",
        als_version=als_version,
    )

    _populate_visits(meta, als_data["folders"])

    _populate_form_classification(meta, form_classification)

    _populate_bronze_dictionary(meta, als_data["fields"], form_classification)

    _create_bronze_tables(db, als_data["forms"], als_data["fields"])

    classification_summary = {
        "occurrence": len(
            [f for f in form_classification.values() if f["schema"] == "occurrence"]
        ),
        "baseline": len(
            [f for f in form_classification.values() if f["schema"] == "baseline"]
        ),
        "longitudinal": len(
            [f for f in form_classification.values() if f["schema"] == "longitudinal"]
        ),
        "unknown": len(
            [f for f in form_classification.values() if f["schema"] == "unknown"]
        ),
    }

    result = {
        "study_code": study_code,
        "als_version": als_version,
        "forms_total": len(als_data["forms"]),
        "fields_total": len(als_data["fields"]),
        "folders_total": len(als_data["folders"]),
        "codelists_total": len(als_data["codelists"]),
        "bronze_tables": len(als_data["forms"]),
        "classification": classification_summary,
    }

    logger.info(f"ALS parsing complete: {result}")
    return result


def _populate_visits(meta: MetadataManager, folders: List[Dict]) -> None:
    logger.info("Populating meta.visits...")

    for folder in folders:
        visit_id = folder["oid"].lower()
        visit_name = folder["oid"]
        visit_label = folder["name"]
        visitnum = folder.get("ordinal")

        is_baseline = any(
            pattern in folder["oid"].upper() for pattern in BASELINE_FOLDER_PATTERNS
        )

        meta.add_visit(
            visit_id=visit_id,
            visit_name=visit_name,
            visitnum=visitnum,
            visit_label=visit_label,
            is_baseline=is_baseline,
        )

    logger.info(f"Visits populated: {len(folders)} records")


def _populate_form_classification(
    meta: MetadataManager,
    form_classification: Dict[str, Dict[str, Any]],
) -> None:
    logger.info("Populating meta.form_classification...")

    for form_oid, info in form_classification.items():
        meta.add_form_classification(
            form_oid=form_oid,
            domain=info.get("domain"),
            schema=info["schema"],
            source_forms=info.get("source_forms", [form_oid]),
            confidence=info.get("confidence", "medium"),
        )

    logger.info(f"Form classification populated: {len(form_classification)} records")


def _populate_bronze_dictionary(
    meta: MetadataManager,
    fields: List[Dict],
    form_classification: Dict[str, Dict[str, Any]],
) -> None:
    logger.info("Populating meta.bronze_dictionary...")

    count = 0
    for field in fields:
        form_oid = field["form_oid"]
        var_name = (field.get("variable_oid") or field["field_oid"]).lower()

        classification = form_classification.get(form_oid, {})
        schema = classification.get("schema", "unknown")

        meta.add_bronze_variable(
            var_name=var_name,
            form_oid=form_oid.lower(),
            field_oid=field["field_oid"],
            var_label=field.get("label"),
            data_type=_infer_data_type(field.get("data_format", "")),
            schema=schema,
            codelist_ref=field.get("codelist_name"),
        )
        count += 1

    logger.info(f"Bronze dictionary populated: {count} records")


def _create_bronze_tables(
    db: Database,
    forms: List[Dict],
    fields: List[Dict],
) -> None:
    logger.info("Creating bronze tables...")

    count = 0
    for form in forms:
        form_oid = form["oid"]

        if not form.get("active", True):
            continue

        ddl = generate_bronze_ddl(form_oid, fields)
        db.execute(ddl)
        count += 1

    logger.info(f"Bronze tables created: {count}")


def parse_als(als_path: str) -> Dict[str, Any]:
    return _parse_als_file(Path(als_path))


def get_domain_field_mapping() -> Dict[str, Dict[str, Optional[str]]]:
    return {
        "AE": {
            "term": "aeterm",
            "startdt": "aestdtc",
            "enddt": "aeendtc",
            "coding_high": "aesoc",
            "coding_low": "aedecod",
        },
        "CM": {
            "term": "cmtrt",
            "startdt": "cmstdtc",
            "enddt": "cmendtc",
            "coding_high": "cmatc1",
            "coding_low": "cmdecod",
        },
        "MH": {
            "term": "mhterm",
            "startdt": "mhstdtc",
            "enddt": "mhendtc",
            "coding_high": "mhsoc",
            "coding_low": "mhdecod",
        },
    }
