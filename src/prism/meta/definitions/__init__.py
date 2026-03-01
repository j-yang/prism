"""Meta Definition Generation.

This module generates meta definitions from mock shells using LLM.
Definitions describe WHAT variables are, not HOW to derive them.
"""

from .agent import DefinitionAgent, ExtractedElement
from .models import (
    GoldStatisticDefinition,
    MetaDefinitions,
    ParamDefinition,
    PlatinumDeliverableDefinition,
    SilverVariableDefinition,
)

__all__ = [
    "DefinitionAgent",
    "ExtractedElement",
    "MetaDefinitions",
    "SilverVariableDefinition",
    "ParamDefinition",
    "GoldStatisticDefinition",
    "PlatinumDeliverableDefinition",
]
