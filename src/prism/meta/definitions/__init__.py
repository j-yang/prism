"""Meta Definition Generation.

This module provides models for meta definitions generated from mock shells.
Definitions describe WHAT variables are, not HOW to derive them.
"""

from .models import (
    GoldStatisticDefinition,
    MetaDefinitions,
    ParamDefinition,
    PlatinumDeliverableDefinition,
    SilverVariableDefinition,
)

__all__ = [
    "MetaDefinitions",
    "SilverVariableDefinition",
    "ParamDefinition",
    "GoldStatisticDefinition",
    "PlatinumDeliverableDefinition",
]
