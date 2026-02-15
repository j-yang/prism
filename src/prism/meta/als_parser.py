"""
ALS Parser for PRISM

Parses Annotated Label Specification (ALS) files and generates:
1. Bronze layer tables (baseline, longitudinal, occurrence)
2. Meta tables (study_info, visits, form_classification)
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
import json
import re
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

DOMAIN_FIELD_MAPPING: Dict[str, Dict[str, Optional[str]]] = {
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
    "PR": {
        "term": "PRTRT",
        "startdt": "PRSTDTC",
        "enddt": "PRENDTC",
        "coding_high": "PRATC1",
        "coding_low": "PRDECOD",
    },
    "DEATH": {
        "term": "DSTERM",
        "startdt": "DSSTDTC",
        "enddt": None,
        "coding_high": None,
        "coding_low": None,
    },
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
        study_code=study_code,
        als_version=als_version,
    )

    _populate_visits(meta, als_data["folders"])

    _populate_form_classification(meta, form_classification)

    result = {
        "study_code": study_code,
        "als_version": als_version,
        "forms_total": len(als_data["forms"]),
        "fields_total": len(als_data["fields"]),
        "folders_total": len(als_data["folders"]),
        "codelists_total": len(als_data["codelists"]),
        "classification": {
            "occurrence": len(
                [f for f in form_classification.values() if f["schema"] == "occurrence"]
            ),
            "baseline": len(
                [f for f in form_classification.values() if f["schema"] == "baseline"]
            ),
            "longitudinal": len(
                [
                    f
                    for f in form_classification.values()
                    if f["schema"] == "longitudinal"
                ]
            ),
            "unknown": len(
                [f for f in form_classification.values() if f["schema"] == "unknown"]
            ),
        },
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


def parse_als(als_path: str) -> Dict[str, Any]:
    return _parse_als_file(Path(als_path))


def get_domain_field_mapping() -> Dict[str, Dict[str, Optional[str]]]:
    return DOMAIN_FIELD_MAPPING.copy()


def set_domain_field_mapping(mapping: Dict[str, Dict[str, Optional[str]]]) -> None:
    global DOMAIN_FIELD_MAPPING
    DOMAIN_FIELD_MAPPING = {k: dict(v) for k, v in mapping.items()}
