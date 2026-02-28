"""PRISM Core Models.

Single source of truth for all data schemas.
Pydantic models define the structure, SQL DDL is auto-generated.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class SchemaType(str, Enum):
    """Data schema types for medallion architecture."""

    BASELINE = "baseline"
    LONGITUDINAL = "longitudinal"
    OCCURRENCE = "occurrence"


class DataType(str, Enum):
    """Data types for variables."""

    TEXT = "TEXT"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    DATE = "DATE"
    DATETIME = "DATETIME"
    BOOLEAN = "BOOLEAN"


class TransformationType(str, Enum):
    """Types of transformations."""

    DIRECT = "direct"
    PYTHON = "python"
    RULE_DOC = "rule_doc"


class DeliverableType(str, Enum):
    """Types of deliverables."""

    TABLE = "table"
    LISTING = "listing"
    FIGURE = "figure"


class ParamCategory(str, Enum):
    """Parameter categories."""

    EFFICACY = "efficacy"
    SAFETY = "safety"
    PK = "pk"
    PD = "pd"


class ElementType(str, Enum):
    """Types of elements in deliverables."""

    VARIABLE = "variable"
    PARAM = "param"
    FLAG = "flag"


# ============================================================================
# Meta Layer Models
# ============================================================================


class StudyInfo(BaseModel):
    """Study basic information (meta.study_info)."""

    studyid: str = Field(..., description="Study identifier")
    indication: Optional[str] = Field(None, description="Therapeutic indication")
    description: Optional[str] = Field(None, description="Study description")
    als_version: Optional[str] = Field(None, description="ALS version")
    spec_version: Optional[str] = Field(None, description="Spec version")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Param(BaseModel):
    """Longitudinal parameter definition (meta.params)."""

    paramcd: str = Field(..., description="Parameter code (unique identifier)")
    parameter: str = Field(..., description="Full parameter name")
    param_desc: Optional[str] = Field(None, description="Parameter description")
    category: Optional[str] = Field(
        None, description="Category (Efficacy/Safety/PK/PD)"
    )
    data_type: Optional[str] = Field(None, description="Data type")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    default_source_form: Optional[str] = Field(None, description="Default source form")
    default_source_var: Optional[str] = Field(
        None, description="Default source variable"
    )
    default_aval_expr: Optional[str] = Field(
        None, description="Default AVAL expression"
    )
    has_baseline: bool = Field(True, description="Has baseline value")
    baseline_definition: Optional[str] = Field(None, description="Baseline definition")
    is_external: bool = Field(False, description="Is external data")
    external_source: Optional[str] = Field(None, description="External source")
    display_order: Optional[int] = Field(None, description="Display order")
    created_at: Optional[datetime] = None


class Visit(BaseModel):
    """Analysis visit definition (meta.visits)."""

    visit_id: str = Field(..., description="Visit identifier")
    visitnum: Optional[int] = Field(None, description="Visit number")
    visit_name: str = Field(..., description="Visit name")
    visit_label: Optional[str] = Field(None, description="Visit label")
    visit_type: Optional[str] = Field(None, description="Visit type")
    is_baseline: bool = Field(False, description="Is baseline visit")
    is_endpoint: bool = Field(False, description="Is endpoint visit")
    target_day: Optional[int] = Field(None, description="Target day")
    window_lower: Optional[int] = Field(None, description="Window lower bound")
    window_upper: Optional[int] = Field(None, description="Window upper bound")
    display_order: Optional[int] = Field(None, description="Display order")
    created_at: Optional[datetime] = None


class BronzeVariable(BaseModel):
    """Bronze layer variable (meta.bronze_dictionary)."""

    var_name: str = Field(..., description="Variable name")
    form_oid: str = Field(..., description="Form OID")
    schema: str = Field(..., description="Schema (baseline/longitudinal/occurrence)")
    field_oid: Optional[str] = Field(None, description="Field OID from EDC")
    var_label: Optional[str] = Field(None, description="Variable label")
    data_type: Optional[str] = Field(None, description="Data type")
    is_required: bool = Field(False, description="Is required field")
    codelist_ref: Optional[str] = Field(None, description="Codelist reference")
    created_at: Optional[datetime] = None


class SilverVariable(BaseModel):
    """Silver layer variable (meta.silver_dictionary)."""

    var_name: str = Field(..., description="Variable name (snake_case)")
    var_label: Optional[str] = Field(None, description="Human readable label")
    schema: str = Field(..., description="Schema (baseline/longitudinal/occurrence)")
    data_type: Optional[str] = Field(None, description="Data type")
    source_vars: Optional[str] = Field(
        None, description="Comma-separated source variables"
    )
    transformation: Optional[str] = Field(
        None, description="Python transformation code"
    )
    transformation_type: str = Field("direct", description="Transformation type")
    rule_doc_path: Optional[str] = Field(None, description="Rule document path")
    description: Optional[str] = Field(None, description="Description")
    param_ref: Optional[str] = Field(None, description="Reference to paramcd")
    display_order: Optional[int] = Field(None, description="Display order")
    created_at: Optional[datetime] = None


class GoldStatistic(BaseModel):
    """Gold layer statistic (meta.gold_dictionary)."""

    element_id: str = Field(..., description="Element identifier (var_name/paramcd)")
    group_id: str = Field(..., description="Group identifier (treatment group)")
    schema: str = Field(..., description="Schema")
    population: Optional[str] = Field(None, description="Population filter")
    selection: Optional[str] = Field(None, description="Selection criteria")
    statistics: Optional[dict] = Field(None, description="Statistics definition")
    deliverable_id: Optional[str] = Field(None, description="Deliverable ID")
    description: Optional[str] = Field(None, description="Description")
    unit: Optional[str] = Field(None, description="Unit")
    display_order: Optional[int] = Field(None, description="Display order")
    created_at: Optional[datetime] = None


class PlatinumDeliverable(BaseModel):
    """Platinum layer deliverable (meta.platinum_dictionary)."""

    deliverable_id: str = Field(..., description="Deliverable identifier")
    deliverable_type: str = Field(
        ..., description="Deliverable type (table/listing/figure)"
    )
    title: Optional[str] = Field(None, description="Title")
    schema: Optional[str] = Field(None, description="Schema")
    elements: Optional[List[dict]] = Field(None, description="Elements in deliverable")
    population: Optional[str] = Field(None, description="Population")
    section: Optional[str] = Field(None, description="Section")
    display_order: Optional[int] = Field(None, description="Display order")
    created_at: Optional[datetime] = None


class FormClassification(BaseModel):
    """Form classification mapping (meta.form_classification)."""

    form_oid: str = Field(..., description="Form OID")
    domain: Optional[str] = Field(None, description="Domain")
    schema: str = Field(..., description="Schema")
    source_forms: Optional[List[str]] = Field(None, description="Source forms")
    classification_confidence: Optional[str] = Field(
        None, description="Classification confidence"
    )
    created_at: Optional[datetime] = None


class Dependency(BaseModel):
    """Variable dependency (meta.dependencies)."""

    from_var: str = Field(..., description="Source variable")
    to_var: str = Field(..., description="Target variable")


# ============================================================================
# Spec Output Models (LLM generates these)
# ============================================================================


class SilverVariableSpec(SilverVariable):
    """Spec output for silver variable - extends SilverVariable."""

    confidence: str = Field(
        "medium", description="Generation confidence (high/medium/low)"
    )
    used_in: Optional[str] = Field(None, description="Comma-separated deliverable IDs")


class ParamSpec(Param):
    """Spec output for param - extends Param with generation metadata."""

    used_in: Optional[str] = Field(None, description="Comma-separated deliverable IDs")


class GoldStatisticSpec(GoldStatistic):
    """Spec output for gold statistic."""

    row_label: Optional[str] = Field(None, description="Row label in table")
    element_type: Optional[str] = Field(
        None, description="Element type (variable/param/flag)"
    )
    group_by: Optional[List[str]] = Field(None, description="Group by columns")


class PlatinumDeliverableSpec(PlatinumDeliverable):
    """Spec output for platinum deliverable."""

    pass


class GeneratedSpec(BaseModel):
    """Complete generated specification from LLM."""

    silver_variables: List[SilverVariableSpec] = Field(default_factory=list)
    params: List[ParamSpec] = Field(default_factory=list)
    gold_statistics: List[GoldStatisticSpec] = Field(default_factory=list)
    platinum: List[PlatinumDeliverableSpec] = Field(default_factory=list)
    confidence_notes: List[str] = Field(default_factory=list)


# ============================================================================
# Schema for LLM Batch Generation
# ============================================================================


class ElementForGeneration(BaseModel):
    """Element extracted from mock shell for LLM generation."""

    label: str = Field(..., description="Element label")
    type: str = Field(..., description="Element type (row_label/column/param)")
    used_in: List[str] = Field(default_factory=list, description="Deliverable IDs")
    context: str = Field("", description="Context information")


class BatchGenerationInput(BaseModel):
    """Input for batch variable generation."""

    elements: List[ElementForGeneration] = Field(default_factory=list)
    als_vars: List[dict] = Field(default_factory=list)
    patterns: List[dict] = Field(default_factory=list)
