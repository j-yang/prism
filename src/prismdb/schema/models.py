"""
PRISM-DB Meta Schema Models

Pydantic models corresponding to the 11 metadata tables.
Used for Agent parsing, validation, and code generation.
"""

from enum import Enum
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class SchemaType(str, Enum):
    """Data schema types"""

    BASELINE = "baseline"
    LONGITUDINAL = "longitudinal"
    OCCURRENCE = "occurrence"


class DataType(str, Enum):
    """Variable data types"""

    NUMERIC = "numeric"
    CHARACTER = "character"
    DATE = "date"
    FLAG = "flag"


class OutputType(str, Enum):
    """Output types"""

    TABLE = "table"
    LISTING = "listing"
    FIGURE = "figure"


class TransformationType(str, Enum):
    """Transformation types"""

    DIRECT = "direct"
    SQL = "sql"
    FUNCTION = "function"
    RULE_DOC = "rule_doc"


class Complexity(str, Enum):
    """Derivation complexity levels"""

    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


class ParamCategory(str, Enum):
    """Parameter categories"""

    EFFICACY = "efficacy"
    SAFETY = "safety"
    PK = "pk"
    PD = "pd"


class VisitType(str, Enum):
    """Visit types"""

    SCHEDULED = "scheduled"
    UNSCHEDULED = "unscheduled"
    EARLY_TERM = "early_term"


class ImplType(str, Enum):
    """Implementation types for functions"""

    SQL = "sql"
    R = "r"
    PYTHON = "python"


class StudyInfo(BaseModel):
    """Study基本信息"""

    study_code: str
    indication: Optional[str] = None
    description: Optional[str] = None
    als_version: Optional[str] = None
    spec_version: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Parameter(BaseModel):
    """Longitudinal参数定义（可外链）"""

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
    """Occurrence事件标志定义（可外链）"""

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
    """分析用Visit定义"""

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
    """统一的变量注册表"""

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
    """变量/参数的衍生规则"""

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
    """输出定义"""

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
    """输出-变量关联"""

    id: Optional[int] = None
    output_id: str
    var_id: str
    role: Optional[str] = None
    display_label: Optional[str] = None
    display_order: Optional[int] = None


class OutputParam(BaseModel):
    """输出-参数关联"""

    id: Optional[int] = None
    output_id: str
    paramcd: str
    display_order: Optional[int] = None


class Function(BaseModel):
    """复杂函数/计算逻辑"""

    function_id: str
    function_name: str
    description: Optional[str] = None
    impl_type: str
    impl_code: Optional[str] = None
    input_params: Optional[dict] = None
    output_type: Optional[str] = None
    created_at: Optional[datetime] = None


class Dependency(BaseModel):
    """变量间的依赖关系"""

    id: Optional[int] = None
    from_var: str
    to_var: str
