"""PRISM Spec Agent.

Generate clinical trial specifications from mock shell documents.
"""

from prism.spec.extractor import (
    MockShellExtractor,
    MockShellContext,
    Deliverable,
    extract_mock_shell,
)
from prism.spec.generator import (
    SpecGenerator,
    GeneratedSpec,
    generate_spec,
)
from prism.spec.matcher import (
    ALSMatcher,
    MatchResult,
    load_als_dict,
    match_als_variables,
)
from prism.spec.learner import (
    DiffLearner,
    DiffChange,
    LearnedPattern,
    learn_from_correction,
)
from prism.spec.memory import (
    MemoryStore,
    Pattern,
    get_memory_store,
)
from prism.spec.excel_writer import (
    SpecExcelWriter,
    write_spec_excel,
)

__all__ = [
    "MockShellExtractor",
    "MockShellContext",
    "Deliverable",
    "extract_mock_shell",
    "SpecGenerator",
    "GeneratedSpec",
    "generate_spec",
    "ALSMatcher",
    "MatchResult",
    "load_als_dict",
    "match_als_variables",
    "DiffLearner",
    "DiffChange",
    "LearnedPattern",
    "learn_from_correction",
    "MemoryStore",
    "Pattern",
    "get_memory_store",
    "SpecExcelWriter",
    "write_spec_excel",
]
