"""Meta Definition Models.

Output of Step 1: Meta definitions generated from mock shell.
These are DEFINITIONS (what variables are), not IMPLEMENTATIONS (how to derive them).
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class SilverVariableDefinition(BaseModel):
    """Silver variable definition - describes what the variable is."""

    var_name: str = Field(..., description="Variable name (snake_case)")
    var_label: str = Field(..., description="Human readable label")
    schema: str = Field(..., description="baseline|occurrence|longitudinal")
    data_type: str = Field(..., description="TEXT|INTEGER|FLOAT|DATE|DATETIME")
    description: str = Field(..., description="What this variable represents")
    used_in: List[str] = Field(
        default_factory=list, description="Deliverable IDs where this is used"
    )
    confidence: str = Field("medium", description="high|medium|low")

    source_vars: Optional[str] = None
    transformation: Optional[str] = None
    transformation_type: str = "direct"
    param_ref: Optional[str] = None


class ParamDefinition(BaseModel):
    """Parameter definition for longitudinal data."""

    paramcd: str = Field(..., description="Parameter code")
    parameter: str = Field(..., description="Full parameter name")
    category: Optional[str] = Field(None, description="Efficacy|Safety|PK|PD")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    used_in: List[str] = Field(
        default_factory=list, description="Deliverable IDs where this is used"
    )

    param_desc: Optional[str] = None
    data_type: Optional[str] = None
    default_source_form: Optional[str] = None
    default_source_var: Optional[str] = None
    default_aval_expr: Optional[str] = None
    has_baseline: bool = True
    baseline_definition: Optional[str] = None
    is_external: bool = False
    external_source: Optional[str] = None
    display_order: Optional[int] = None


class GoldStatisticDefinition(BaseModel):
    """Gold statistic definition - describes what statistics to calculate."""

    element_id: str = Field(..., description="Variable or param ID")
    element_type: str = Field(..., description="variable|param|flag")
    row_label: str = Field(..., description="Row label in table")
    schema: str = Field(..., description="baseline|occurrence|longitudinal")
    statistics: Dict = Field(..., description="n, %, mean, median, etc.")
    group_by: List[str] = Field(default_factory=list, description="Grouping columns")
    deliverable_id: str = Field(..., description="Which deliverable")
    confidence: str = Field("medium", description="high|medium|low")

    group_id: str = "all"
    population: Optional[str] = None
    selection: Optional[str] = None
    description: Optional[str] = None
    unit: Optional[str] = None
    display_order: Optional[int] = None


class PlatinumDeliverableDefinition(BaseModel):
    """Platinum deliverable definition."""

    deliverable_id: str = Field(..., description="e.g., 14.1.2.1")
    deliverable_type: str = Field(..., description="table|listing|figure")
    title: str = Field(..., description="Deliverable title")
    population: Optional[str] = Field(None, description="Safety Set, FAS, etc.")
    schema: Optional[str] = Field(None, description="Primary schema")
    elements: List[Dict] = Field(
        default_factory=list, description="Elements in this deliverable"
    )

    section: Optional[str] = None
    display_order: Optional[int] = None


class MetaDefinitions(BaseModel):
    """Complete meta definitions generated from mock shell.

    This is the output of Step 1: Mock Shell → Meta Definitions.
    """

    silver_variables: List[SilverVariableDefinition] = Field(default_factory=list)
    params: List[ParamDefinition] = Field(default_factory=list)
    gold_statistics: List[GoldStatisticDefinition] = Field(default_factory=list)
    platinum_deliverables: List[PlatinumDeliverableDefinition] = Field(
        default_factory=list
    )
    confidence_notes: List[str] = Field(
        default_factory=list, description="Items needing human review"
    )
