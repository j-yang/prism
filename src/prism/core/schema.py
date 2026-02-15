from enum import Enum
from typing import Optional, List
from datetime import datetime
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


class OutputType(str, Enum):
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
    study_code: str
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


class Variable(BaseModel):
    var_id: str
    var_name: str
    var_label: Optional[str] = None
    schema: str
    block: Optional[str] = None
    data_type: Optional[str] = None
    param_ref: Optional[str] = None
    flag_ref: Optional[str] = None
    is_baseline_of_param: bool = False
    display_order: Optional[int] = None
    created_at: Optional[datetime] = None


class Derivation(BaseModel):
    deriv_id: str
    target_var: str
    source_vars: Optional[List[str]] = None
    source_tables: Optional[List[str]] = None
    transformation: str
    transformation_type: Optional[str] = None
    function_id: Optional[str] = None
    rule_doc_path: Optional[str] = None
    complexity: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        json_encoders = {list: lambda v: v if isinstance(v, str) else str(v)}


class Output(BaseModel):
    output_id: str
    output_type: str
    title: Optional[str] = None
    schema: str
    source_block: Optional[str] = None
    population: Optional[str] = None
    visit_filter: Optional[str] = None
    filter_expr: Optional[str] = None
    render_function: Optional[str] = None
    render_options: Optional[dict] = None
    section: Optional[str] = None
    display_order: Optional[int] = None
    created_at: Optional[datetime] = None


class OutputVariable(BaseModel):
    id: Optional[int] = None
    output_id: str
    var_id: str
    role: Optional[str] = None
    display_label: Optional[str] = None
    display_order: Optional[int] = None


class OutputParam(BaseModel):
    id: Optional[int] = None
    output_id: str
    paramcd: str
    display_order: Optional[int] = None


class Function(BaseModel):
    function_id: str
    function_name: str
    description: Optional[str] = None
    impl_type: str
    impl_code: Optional[str] = None
    input_params: Optional[dict] = None
    output_type: Optional[str] = None
    created_at: Optional[datetime] = None


class Dependency(BaseModel):
    id: Optional[int] = None
    from_var: str
    to_var: str
