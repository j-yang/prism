from .config import get_sql_path, get_template_path
from .database import Database, get_connection, init_database

# New models (single source of truth)
from .models import (
    BatchGenerationInput,
    BronzeVariable,
    DataType,
    DeliverableType,
    Dependency,
    ElementForGeneration,
    ElementType,
    FormClassification,
    GeneratedSpec,
    GoldStatistic,
    GoldStatisticSpec,
    Param,
    ParamCategory,
    ParamSpec,
    PlatinumDeliverable,
    PlatinumDeliverableSpec,
    SchemaType,
    SilverVariable,
    SilverVariableSpec,
    StudyInfo,
    TransformationType,
    Visit,
)

# Legacy imports for backward compatibility
from .schema import (
    Complexity,
    Flag,
    ImplType,
    Parameter,
    VisitType,
)

__all__ = [
    "Database",
    "init_database",
    "get_connection",
    "get_sql_path",
    "get_template_path",
    # New models
    "SchemaType",
    "DataType",
    "TransformationType",
    "DeliverableType",
    "ParamCategory",
    "ElementType",
    "StudyInfo",
    "Param",
    "Visit",
    "BronzeVariable",
    "SilverVariable",
    "GoldStatistic",
    "PlatinumDeliverable",
    "FormClassification",
    "Dependency",
    "SilverVariableSpec",
    "ParamSpec",
    "GoldStatisticSpec",
    "PlatinumDeliverableSpec",
    "GeneratedSpec",
    "ElementForGeneration",
    "BatchGenerationInput",
    # Legacy
    "Parameter",
    "Flag",
    "Complexity",
    "VisitType",
    "ImplType",
]
