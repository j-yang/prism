"""Definition Agent - Generate meta definitions from mock shell.

This agent uses LLM to understand mock shell semantics and generate
meta DEFINITIONS (what variables are), not IMPLEMENTATIONS (how to derive them).
"""

import json
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from prism.agent.base import BaseAgent
from prism.meta.extractor import Deliverable, MockShellContext

from .models import MetaDefinitions
from .templates import TEMPLATE_BATCH_DELIVERABLES


@dataclass
class ExtractedElement:
    """An element extracted from mock shell."""

    label: str
    element_type: str
    deliverable_ids: List[str] = field(default_factory=list)
    context: str = ""


class DefinitionAgent(BaseAgent):
    """LLM Agent for generating meta definitions from mock shell."""

    def __init__(self, provider: str = "deepseek"):
        super().__init__(provider=provider)

    def _get_system_prompt(self) -> str:
        return """You are a clinical trial metadata expert.

Your task is to understand mock shell documents and generate meta DEFINITIONS.

IMPORTANT: 
- Generate DEFINITIONS (what variables are), not IMPLEMENTATIONS (how to derive them)
- Use semantic understanding from table structure, footnotes, and context
- DO NOT try to map to ALS fields or data sources

For each element:
1. Understand its semantic meaning from context
2. Classify as variable, parameter, or flag
3. Determine schema (baseline/occurrence/longitudinal)
4. Infer data type from context
5. Describe what it represents in 'description' field

Output ONLY valid JSON matching the MetaDefinitions schema.
"""

    def generate_definitions(
        self,
        mock_context: MockShellContext,
        deliverable_ids: Optional[List[str]] = None,
    ) -> MetaDefinitions:
        """Generate meta definitions from mock shell context.

        Args:
            mock_context: Extracted mock shell data
            deliverable_ids: Optional filter for specific deliverables

        Returns:
            MetaDefinitions with all variables, params, statistics, deliverables
        """
        deliverables = mock_context.deliverables
        if deliverable_ids:
            deliverables = [
                d for d in deliverables if d.deliverable_id in deliverable_ids
            ]

        elements = self._extract_elements(deliverables)

        all_defs = MetaDefinitions()
        batch_size = 10

        for i in range(0, len(deliverables), batch_size):
            batch_deliverables = deliverables[i : i + batch_size]
            batch_element_keys = set()
            for d in batch_deliverables:
                for key, elem in elements.items():
                    if d.deliverable_id in elem.deliverable_ids:
                        batch_element_keys.add(key)

            batch_elements = {
                k: elements[k] for k in batch_element_keys if k in elements
            }

            print(
                f"  Batch {i // batch_size + 1}: "
                f"{len(batch_deliverables)} deliverables, "
                f"{len(batch_elements)} elements"
            )

            batch_defs = self._generate_batch_definitions(
                batch_deliverables, batch_elements, mock_context
            )

            all_defs.silver_variables.extend(batch_defs.silver_variables)
            all_defs.params.extend(batch_defs.params)
            all_defs.gold_statistics.extend(batch_defs.gold_statistics)
            all_defs.platinum_deliverables.extend(batch_defs.platinum_deliverables)
            all_defs.confidence_notes.extend(batch_defs.confidence_notes)

        all_defs = self._deduplicate(all_defs)

        return all_defs

    def _extract_elements(
        self, deliverables: List[Deliverable]
    ) -> Dict[str, ExtractedElement]:
        """Extract unique elements from deliverables."""
        elements = {}

        for d in deliverables:
            if d.table_data and len(d.table_data) > 0:
                for row in d.table_data[1:]:
                    if row and row[0]:
                        label = str(row[0]).strip()
                        if label and not label.startswith("<<") and label != "N=xxx":
                            key = self._normalize_label(label)
                            if key not in elements:
                                elements[key] = ExtractedElement(
                                    label=label,
                                    element_type="row_label",
                                    deliverable_ids=[],
                                    context=(
                                        f"Row in {d.deliverable_type} "
                                        f"{d.deliverable_id}"
                                    ),
                                )
                            if d.deliverable_id not in elements[key].deliverable_ids:
                                elements[key].deliverable_ids.append(d.deliverable_id)

                for col in d.table_data[0]:
                    col = str(col).strip()
                    if (
                        col
                        and not col.startswith("<<")
                        and col not in ["N=xxx", "n (%)", "Total"]
                    ):
                        key = self._normalize_label(col)
                        if key not in elements:
                            elements[key] = ExtractedElement(
                                label=col,
                                element_type="column",
                                deliverable_ids=[],
                                context=(
                                    f"Column in {d.deliverable_type} {d.deliverable_id}"
                                ),
                            )
                        if d.deliverable_id not in elements[key].deliverable_ids:
                            elements[key].deliverable_ids.append(d.deliverable_id)

        return elements

    def _generate_batch_definitions(
        self,
        deliverables: List[Deliverable],
        elements: Dict[str, ExtractedElement],
        context: MockShellContext,
    ) -> MetaDefinitions:
        """Generate definitions for a batch of deliverables."""
        prompt = self._build_prompt(deliverables, elements, context)

        result = self.run(prompt, result_type=MetaDefinitions)

        return result or MetaDefinitions()

    def _build_prompt(
        self,
        deliverables: List[Deliverable],
        elements: Dict[str, ExtractedElement],
        context: MockShellContext,
    ) -> str:
        """Build LLM prompt from mock shell context."""
        deliverables_json = json.dumps(
            [
                {
                    "id": d.deliverable_id,
                    "type": d.deliverable_type,
                    "title": d.title,
                    "population": d.population,
                    "table_data": d.table_data[:5] if d.table_data else [],
                    "footnotes": dict(list(d.footnotes.items())[:5]),
                    "programming_notes": d.programming_notes[:3],
                }
                for d in deliverables
            ],
            indent=2,
            ensure_ascii=False,
        )

        elements_json = json.dumps(
            [
                {
                    "label": e.label,
                    "type": e.element_type,
                    "used_in": list(set(e.deliverable_ids)),
                    "context": e.context,
                }
                for e in elements.values()
            ],
            indent=2,
            ensure_ascii=False,
        )

        prompt = TEMPLATE_BATCH_DELIVERABLES.format(
            study_title=context.study_title,
            protocol_no=context.protocol_no,
            num_deliverables=len(deliverables),
            deliverables_json=deliverables_json,
            elements_json=elements_json,
        )

        return prompt

    def _normalize_label(self, label: str) -> str:
        """Normalize label for deduplication."""
        label = label.lower().strip()
        label = re.sub(r"\[.*?\]", "", label)
        label = re.sub(r"\(.*?\)", "", label)
        label = re.sub(r"\s+", " ", label)
        return label.strip()

    def _deduplicate(self, defs: MetaDefinitions) -> MetaDefinitions:
        """Remove duplicate variables and params."""
        seen_vars = {}
        for v in defs.silver_variables:
            if v.var_name not in seen_vars:
                seen_vars[v.var_name] = v
            else:
                existing = seen_vars[v.var_name]
                existing.used_in = list(set(existing.used_in + v.used_in))

        defs.silver_variables = list(seen_vars.values())

        seen_params = {}
        for p in defs.params:
            if p.paramcd not in seen_params:
                seen_params[p.paramcd] = p
            else:
                existing = seen_params[p.paramcd]
                existing.used_in = list(set(existing.used_in + p.used_in))

        defs.params = list(seen_params.values())

        seen_gold = {}
        for g in defs.gold_statistics:
            key = f"{g.deliverable_id}_{g.element_id}"
            if key not in seen_gold:
                seen_gold[key] = g

        defs.gold_statistics = list(seen_gold.values())

        seen_platinum = {}
        for p in defs.platinum_deliverables:
            if p.deliverable_id not in seen_platinum:
                seen_platinum[p.deliverable_id] = p

        defs.platinum_deliverables = list(seen_platinum.values())

        return defs
