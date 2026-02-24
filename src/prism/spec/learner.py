"""Diff Learner.

Learns from human corrections to improve future spec generation.
"""

import json
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import List, Optional

from prism.agent import call_deepseek
from prism.spec.memory import get_memory_store, Pattern
from prism.spec.templates import format_prompt, TEMPLATE_LEARN_DIFF


@dataclass
class DiffChange:
    """A single change between original and corrected spec."""

    field: str
    original: str
    corrected: str
    change_type: str  # 'naming', 'derivation', 'selection', 'statistics'


@dataclass
class LearnedPattern:
    """A pattern extracted from human corrections."""

    pattern_type: str
    input_pattern: str
    original_output: str
    corrected_output: str
    rule: str


class DiffLearner:
    """Learn patterns from human corrections."""

    def __init__(self, memory_db: Optional[str] = None):
        self.memory = get_memory_store(memory_db)

    def compare_specs(self, original: dict, corrected: dict) -> List[DiffChange]:
        """Compare original and corrected specs to find changes.

        Args:
            original: Original generated spec
            corrected: Human-corrected spec

        Returns:
            List of DiffChange objects
        """
        changes = []

        changes.extend(self._compare_silver_variables(original, corrected))
        changes.extend(self._compare_gold_statistics(original, corrected))
        changes.extend(self._compare_params(original, corrected))

        return changes

    def _compare_silver_variables(
        self, original: dict, corrected: dict
    ) -> List[DiffChange]:
        """Compare silver variables between specs."""
        changes = []

        orig_vars = {v.get("var_name"): v for v in original.get("silver_variables", [])}
        corr_vars = {
            v.get("var_name"): v for v in corrected.get("silver_variables", [])
        }

        for var_name, corr_var in corr_vars.items():
            orig_var = orig_vars.get(var_name)

            if not orig_var:
                changes.append(
                    DiffChange(
                        field=f"silver_variables.{var_name}",
                        original="",
                        corrected=json.dumps(corr_var),
                        change_type="naming",
                    )
                )
                continue

            if orig_var.get("derivation") != corr_var.get("derivation"):
                changes.append(
                    DiffChange(
                        field=f"silver_variables.{var_name}.derivation",
                        original=orig_var.get("derivation", ""),
                        corrected=corr_var.get("derivation", ""),
                        change_type="derivation",
                    )
                )

            if orig_var.get("var_name") != corr_var.get("var_name"):
                changes.append(
                    DiffChange(
                        field=f"silver_variables.name",
                        original=orig_var.get("var_name", ""),
                        corrected=corr_var.get("var_name", ""),
                        change_type="naming",
                    )
                )

        return changes

    def _compare_gold_statistics(
        self, original: dict, corrected: dict
    ) -> List[DiffChange]:
        """Compare gold statistics between specs."""
        changes = []

        orig_stats = original.get("gold_statistics", [])
        corr_stats = corrected.get("gold_statistics", [])

        for i, (orig, corr) in enumerate(zip(orig_stats, corr_stats)):
            for key in ["selection", "statistics", "element_id"]:
                if orig.get(key) != corr.get(key):
                    changes.append(
                        DiffChange(
                            field=f"gold_statistics[{i}].{key}",
                            original=str(orig.get(key, "")),
                            corrected=str(corr.get(key, "")),
                            change_type="selection"
                            if key == "selection"
                            else "statistics",
                        )
                    )

        return changes

    def _compare_params(self, original: dict, corrected: dict) -> List[DiffChange]:
        """Compare params between specs."""
        changes = []

        orig_params = {p.get("paramcd"): p for p in original.get("params", [])}
        corr_params = {p.get("paramcd"): p for p in corrected.get("params", [])}

        for paramcd, corr_param in corr_params.items():
            orig_param = orig_params.get(paramcd)

            if orig_param and orig_param.get("source_form") != corr_param.get(
                "source_form"
            ):
                changes.append(
                    DiffChange(
                        field=f"params.{paramcd}.source_form",
                        original=orig_param.get("source_form", ""),
                        corrected=corr_param.get("source_form", ""),
                        change_type="derivation",
                    )
                )

        return changes

    def learn_from_diff(
        self, original: dict, corrected: dict, study_id: str, use_llm: bool = True
    ) -> List[Pattern]:
        """Learn patterns from spec diff.

        Args:
            original: Original generated spec
            corrected: Human-corrected spec
            study_id: Study identifier
            use_llm: Whether to use LLM for pattern extraction

        Returns:
            List of learned Pattern objects
        """
        changes = self.compare_specs(original, corrected)

        if not changes:
            return []

        patterns = []

        if use_llm:
            patterns = self._extract_patterns_with_llm(
                changes, original, corrected, study_id
            )
        else:
            patterns = self._extract_patterns_simple(changes, study_id)

        for pattern in patterns:
            self.memory.add_pattern(pattern)

        self.memory.record_study(study_id, "", patterns_learned=len(patterns))

        return patterns

    def _extract_patterns_with_llm(
        self, changes: List[DiffChange], original: dict, corrected: dict, study_id: str
    ) -> List[Pattern]:
        """Use LLM to extract generalizable patterns from changes."""

        prompt = format_prompt(
            TEMPLATE_LEARN_DIFF,
            original_json=json.dumps(original, indent=2)[:3000],
            corrected_json=json.dumps(corrected, indent=2)[:3000],
        )

        response = call_deepseek(prompt, temperature=0.1)

        patterns = []

        if response:
            try:
                result = json.loads(response)
                for i, p in enumerate(result.get("patterns", [])):
                    import hashlib

                    pattern_id = hashlib.md5(
                        f"{p['pattern_type']}:{p['input_pattern']}".encode()
                    ).hexdigest()[:12]

                    patterns.append(
                        Pattern(
                            pattern_id=pattern_id,
                            pattern_type=p["pattern_type"],
                            input_pattern=p["input_pattern"],
                            output_spec={"corrected": p["corrected_output"]},
                            rule=p["rule"],
                            source_study=study_id,
                        )
                    )
            except json.JSONDecodeError:
                pass

        if not patterns:
            patterns = self._extract_patterns_simple(changes, study_id)

        return patterns

    def _extract_patterns_simple(
        self, changes: List[DiffChange], study_id: str
    ) -> List[Pattern]:
        """Simple pattern extraction without LLM."""
        import hashlib

        patterns = []

        for change in changes:
            pattern_id = hashlib.md5(
                f"{change.change_type}:{change.field}".encode()
            ).hexdigest()[:12]

            patterns.append(
                Pattern(
                    pattern_id=pattern_id,
                    pattern_type=change.change_type,
                    input_pattern=change.field,
                    output_spec={
                        "original": change.original,
                        "corrected": change.corrected,
                    },
                    rule=f"Changed {change.field} from '{change.original}' to '{change.corrected}'",
                    source_study=study_id,
                )
            )

        return patterns


def learn_from_correction(
    original_path: str,
    corrected_path: str,
    study_id: str,
    memory_db: Optional[str] = None,
) -> List[Pattern]:
    """Convenience function to learn from corrected spec files.

    Args:
        original_path: Path to original generated spec JSON
        corrected_path: Path to corrected spec JSON
        study_id: Study identifier
        memory_db: Optional path to memory database

    Returns:
        List of learned Pattern objects
    """
    from pathlib import Path

    original = json.loads(Path(original_path).read_text())
    corrected = json.loads(Path(corrected_path).read_text())

    learner = DiffLearner(memory_db)
    return learner.learn_from_diff(original, corrected, study_id)
