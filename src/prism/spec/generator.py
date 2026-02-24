"""Spec Generator.

Generates clinical trial specifications using LLM.
"""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, List, Dict

from prism.agent import call_deepseek
from prism.spec.extractor import MockShellContext, Deliverable
from prism.spec.matcher import load_als_dict
from prism.spec.memory import get_memory_store
from prism.spec.templates import format_prompt, TEMPLATE_GENERATE_SPEC, SYSTEM_PROMPT


@dataclass
class GeneratedSpec:
    """Complete generated specification for a deliverable."""

    deliverable_id: str
    platinum: dict = field(default_factory=dict)
    silver_variables: list = field(default_factory=list)
    gold_statistics: list = field(default_factory=list)
    params: list = field(default_factory=list)
    study_config: dict = field(default_factory=dict)
    confidence_notes: list = field(default_factory=list)


class SpecGenerator:
    """Generate specifications using LLM."""

    def __init__(self, als_path: Optional[str] = None, memory_db: Optional[str] = None):
        self.als_dict = load_als_dict(als_path) if als_path else {}
        self.memory = get_memory_store(memory_db)

    def generate_for_deliverable(
        self, deliverable: Deliverable, protocol_no: str = "", study_title: str = ""
    ) -> GeneratedSpec:
        """Generate spec for a single deliverable.

        Args:
            deliverable: Deliverable object from extractor
            protocol_no: Protocol number
            study_title: Study title

        Returns:
            GeneratedSpec object
        """
        deliverable_json = json.dumps(asdict(deliverable), indent=2, ensure_ascii=False)

        als_vars_json = json.dumps(
            list(self.als_dict.values())[:100], indent=2, ensure_ascii=False
        )[:6000]

        patterns_json = self.memory.get_patterns_for_prompt(limit=15)

        prompt = format_prompt(
            TEMPLATE_GENERATE_SPEC,
            protocol_no=protocol_no,
            study_title=study_title,
            deliverable_json=deliverable_json,
            als_vars_json=als_vars_json,
            patterns_json=patterns_json,
        )

        response = call_deepseek(prompt, temperature=0.2, timeout=90)

        if response:
            parsed = self._parse_response(response)
            return GeneratedSpec(
                deliverable_id=deliverable.deliverable_id,
                platinum=parsed.get("platinum", {}),
                silver_variables=parsed.get("silver_variables", []),
                gold_statistics=parsed.get("gold_statistics", []),
                params=parsed.get("params", []),
                study_config=parsed.get("study_config", {}),
                confidence_notes=parsed.get("confidence_notes", []),
            )

        return GeneratedSpec(deliverable_id=deliverable.deliverable_id)

    def generate_for_context(
        self, context: MockShellContext, deliverable_ids: Optional[List[str]] = None
    ) -> List[GeneratedSpec]:
        """Generate specs for multiple deliverables.

        Args:
            context: MockShellContext from extractor
            deliverable_ids: Optional list of specific deliverable IDs to process

        Returns:
            List of GeneratedSpec objects
        """
        specs = []

        for deliverable in context.deliverables:
            if deliverable_ids and deliverable.deliverable_id not in deliverable_ids:
                continue

            spec = self.generate_for_deliverable(
                deliverable,
                protocol_no=context.protocol_no,
                study_title=context.study_title,
            )
            specs.append(spec)

        return specs

    def _parse_response(self, response: str) -> dict:
        """Parse LLM response to extract JSON."""
        response = response.strip()

        if response.startswith("```"):
            lines = response.split("\n")
            response = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")

            start = response.find("{")
            end = response.rfind("}")

            if start != -1 and end != -1:
                try:
                    return json.loads(response[start : end + 1])
                except json.JSONDecodeError:
                    pass

            return {}


def generate_spec(
    mock_shell_path: str,
    als_path: str,
    output_path: Optional[str] = None,
    deliverable_ids: Optional[List[str]] = None,
    memory_db: Optional[str] = None,
) -> List[GeneratedSpec]:
    """Convenience function to generate specs.

    Args:
        mock_shell_path: Path to mock shell document
        als_path: Path to ALS Excel file
        output_path: Optional path to save JSON output
        deliverable_ids: Optional list of specific deliverables to process
        memory_db: Optional path to memory database

    Returns:
        List of GeneratedSpec objects
    """
    from prism.spec.extractor import extract_mock_shell

    context = extract_mock_shell(mock_shell_path)
    generator = SpecGenerator(als_path, memory_db)
    specs = generator.generate_for_context(context, deliverable_ids)

    if output_path:
        output_data = {
            "study_title": context.study_title,
            "protocol_no": context.protocol_no,
            "specs": [asdict(s) for s in specs],
        }
        Path(output_path).write_text(
            json.dumps(output_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    return specs
