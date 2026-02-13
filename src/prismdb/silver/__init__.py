"""
PRISM-DB Silver Layer Generator

Generate SQL scripts for Bronze → Silver derivation.
"""

from .generator import SilverGenerator

__all__ = ["SilverGenerator"]
