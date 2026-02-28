from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class SchemaType(str, Enum):
    BASELINE = "baseline"
    LONGITUDINAL = "longitudinal"
    OCCURRENCE = "occurrence"


class DataType(str, Enum):
    NUMERIC = "numeric"
    CHARACTER = "character"
    DATE = "date"
    FLAG = "flag"


class DeliverableType(str, Enum):
    TABLE = "table"
    LISTING = "listing"
    FIGURE = "figure"


class TransformationType(str, Enum):
    DIRECT = "direct"
    SQL = "sql"
    FUNCTION = "function"
    RULE_DOC = "rule_doc"


class Complexity(str, Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


class ParamCategory(str, Enum):
    EFFICACY = "efficacy"
    SAFETY = "safety"
    PK = "pk"
    PD = "pd"


class VisitType(str, Enum):
    SCHEDULED = "scheduled"
    UNSCHEDULED = "unscheduled"
    EARLY_TERM = "early_term"


class ImplType(str, Enum):
    SQL = "sql"
    R = "r"
    PYTHON = "python"


class StudyInfo(BaseModel):
    studyid: str
    indication: Optional[str] = None
    description: Optional[str] = None
    als_version: Optional[str] = None
    spec_version: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Parameter(BaseModel):
    param_id: str
    paramcd: str
    param_label: str
    param_desc: Optional[str] = None
    category: Optional[str] = None
    data_type: Optional[str] = None
    unit: Optional[str] = None
    default_source_form: Optional[str] = None
    default_source_var: Optional[str] = None
    default_aval_expr: Optional[str] = None
    has_baseline: bool = True
    baseline_definition: Optional[str] = None
    is_external: bool = False
    external_source: Optional[str] = None
    display_order: Optional[int] = None
    created_at: Optional[datetime] = None


class Flag(BaseModel):
    flag_id: str
    flag_name: str
    flag_label: str
    flag_desc: Optional[str] = None
    domain: str
    default_condition: Optional[str] = None
    true_value: str = "Y"
    false_value: str = "N"
    is_external: bool = False
    external_source: Optional[str] = None
    display_order: Optional[int] = None
    created_at: Optional[datetime] = None


class Visit(BaseModel):
    visit_id: str
    visitnum: Optional[int] = None
    visit_name: str
    visit_label: Optional[str] = None
    visit_type: Optional[str] = None
    is_baseline: bool = False
    is_endpoint: bool = False
    target_day: Optional[int] = None
    window_lower: Optional[int] = None
    window_upper: Optional[int] = None
    is_external: bool = False
    external_source: Optional[str] = None
    display_order: Optional[int] = None
    created_at: Optional[datetime] = None


class BronzeVariable(BaseModel):
    var_name: str
    form_oid: str
    schema: str
    field_oid: Optional[str] = None
    var_label: Optional[str] = None
    data_type: Optional[str] = None
    is_required: bool = False
    codelist_ref: Optional[str] = None
    created_at: Optional[datetime] = None


class SilverVariable(BaseModel):
    var_name: str
    var_label: Optional[str] = None
    schema: str
    data_type: Optional[str] = None
    source_vars: Optional[str] = None
    transformation: Optional[str] = None
    transformation_type: Optional[str] = None
    rule_doc_path: Optional[str] = None
    description: Optional[str] = None
    param_ref: Optional[str] = None
    display_order: Optional[int] = None
    created_at: Optional[datetime] = None


class GoldVariable(BaseModel):
    var_id: str
    group_id: str
    schema: str
    population: Optional[str] = None
    selection: Optional[str] = None
    statistics: Optional[List] = None
    deliverable_id: Optional[str] = None
    description: Optional[str] = None
    unit: Optional[str] = None
    display_order: Optional[int] = None
    created_at: Optional[datetime] = None


class PlatinumDeliverable(BaseModel):
    deliverable_id: str
    deliverable_type: str
    title: Optional[str] = None
    schema: Optional[str] = None
    elements: Optional[List] = None
    population: Optional[str] = None
    render_function: Optional[str] = None
    render_options: Optional[dict] = None
    section: Optional[str] = None
    display_order: Optional[int] = None
    created_at: Optional[datetime] = None


class Dependency(BaseModel):
    id: Optional[int] = None
    from_var: str
    to_var: str
