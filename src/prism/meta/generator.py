"""Meta Generator.

Generates clinical trial metadata using PydanticAI.
Outputs Pydantic models that match meta schema exactly.
"""

import json
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pydantic import BaseModel

from prism.agent.base import BaseAgent
from prism.core.models import (
    GeneratedSpec,
    GoldStatisticSpec,
    ParamSpec,
    PlatinumDeliverableSpec,
    SilverVariableSpec,
)
from prism.meta.extractor import Deliverable, MockShellContext
from prism.meta.templates import TEMPLATE_BATCH_VARIABLES, TEMPLATE_GOLD_BATCH


@dataclass
class ExtractedElement:
    """An element extracted from mock shell."""

    label: str
    element_type: str
    deliverable_ids: List[str] = field(default_factory=list)
    context: str = ""


class MetaGenerator(BaseAgent):
    """Generate metadata using PydanticAI."""

    def __init__(
        self,
        provider: str = "deepseek",
        als_path: Optional[str] = None,
        db_path: Optional[str] = None,
    ):
        super().__init__(provider=provider, db_path=db_path, als_path=als_path)
        self.tools.load_als_dict(als_path)

    def _get_system_prompt(self) -> str:
        return """You are a clinical trial metadata expert.

Generate Silver layer variable specifications and Gold statistics from mock shell elements.
Output ONLY valid JSON matching the requested schema exactly.

Field naming rules:
- var_name: snake_case (e.g., teae_flg, age_years)
- schema: baseline | occurrence | longitudinal
- data_type: TEXT | INTEGER | FLOAT | DATE | DATETIME
- transformation_type: direct | python | rule_doc
"""

    def _extract_params_from_figure(self, deliverable: Deliverable) -> List[str]:
        """Extract parameter names from figure title."""
        params = []
        title = deliverable.title

        match = re.search(r"Line Plot of (.+?) Overtime", title)
        if match:
            params.append(match.group(1))

        match = re.search(r"Plot of (.+?) Overtime", title)
        if match:
            params.append(match.group(1))

        return params

    def _normalize_label(self, label: str) -> str:
        """Normalize label for deduplication."""
        label = label.lower().strip()
        label = re.sub(r"\[.*?\]", "", label)
        label = re.sub(r"\(.*?\)", "", label)
        label = re.sub(r"\s+", " ", label)
        return label.strip()

    def extract_all_elements(
        self, context: MockShellContext
    ) -> Dict[str, ExtractedElement]:
        """Extract all unique elements from all deliverables."""
        elements = {}

        for deliverable in context.deliverables:
            d_id = deliverable.deliverable_id
            d_type = deliverable.deliverable_type

            if deliverable.deliverable_type == "figure":
                params = self._extract_params_from_figure(deliverable)
                for param in params:
                    if param not in elements:
                        elements[param] = ExtractedElement(
                            label=param,
                            element_type="param",
                            deliverable_ids=[],
                            context=f"Figure parameter for {d_id}",
                        )
                    elements[param].deliverable_ids.append(d_id)

            if deliverable.table_data:
                for row in deliverable.table_data[1:]:
                    if row and row[0]:
                        label = row[0].strip()
                        if (
                            label
                            and not label.startswith("<<")
                            and label not in ["", "N=xxx", "n (%)"]
                            and not re.match(r"^[A-Z]\d{5,}$", label)
                        ):
                            key = self._normalize_label(label)
                            if key not in elements:
                                elements[key] = ExtractedElement(
                                    label=label,
                                    element_type="row_label",
                                    deliverable_ids=[],
                                    context=f"Row in {d_type} {d_id}",
                                )
                            elements[key].deliverable_ids.append(d_id)

                for col in deliverable.table_data[0]:
                    col = str(col).strip()
                    if (
                        col
                        and not col.startswith("<<")
                        and col not in ["N=xxx", "n (%)", "Total", ""]
                    ):
                        key = self._normalize_label(col)
                        if key not in elements:
                            elements[key] = ExtractedElement(
                                label=col,
                                element_type="column",
                                deliverable_ids=[],
                                context=f"Column in {d_type} {d_id}",
                            )
                            elements[key].deliverable_ids.append(d_id)

        return elements

    def generate_variables_batch(
        self,
        elements: Dict[str, ExtractedElement],
        protocol_no: str = "",
        study_title: str = "",
    ) -> GeneratedSpec:
        """Generate all silver variables and params in multiple LLM calls."""
        elements_list = []
        for key, elem in elements.items():
            elements_list.append(
                {
                    "label": elem.label,
                    "type": elem.element_type,
                    "used_in": list(set(elem.deliverable_ids)),
                    "context": elem.context,
                }
            )

        als_vars_json = json.dumps(
            list(self.tools._als_dict.values()), indent=2, ensure_ascii=False
        )

        all_silver_vars = []
        all_params = []
        all_notes = []

        batch_size = 10
        for i in range(0, len(elements_list), batch_size):
            batch = elements_list[i : i + batch_size]
            elements_json = json.dumps(batch, indent=2, ensure_ascii=False)

            prompt = TEMPLATE_BATCH_VARIABLES.format(
                protocol_no=protocol_no,
                study_title=study_title,
                elements_json=elements_json,
                als_vars_json=als_vars_json,
            )
            print(
                f"  Batch {i // batch_size + 1}: {len(batch)} elements, "
                f"prompt size {len(prompt)} chars"
            )

            result = self.run(prompt, result_type=GeneratedSpec)

            if result:
                all_silver_vars.extend(result.silver_variables)
                all_params.extend(result.params)
                all_notes.extend(result.confidence_notes)
                print(f"    Generated {len(result.silver_variables)} variables")
            else:
                print("    No response or validation failed")

        return GeneratedSpec(
            silver_variables=all_silver_vars,
            params=all_params,
            confidence_notes=all_notes,
        )

    def generate_gold_batch(
        self,
        deliverables: List[Deliverable],
        silver_variables: List[SilverVariableSpec],
        params: List[ParamSpec],
    ) -> List[GeneratedSpec]:
        """Generate gold statistics for multiple deliverables in batch."""
        deliverables_json = json.dumps(
            [
                {
                    "id": d.deliverable_id,
                    "type": d.deliverable_type,
                    "title": d.title,
                    "population": d.population,
                    "table_data": d.table_data[:5] if d.table_data else [],
                }
                for d in deliverables
            ],
            indent=2,
            ensure_ascii=False,
        )[:10000]

        vars_json = json.dumps(
            [
                {"var_name": v.var_name, "schema": v.schema}
                for v in silver_variables[:50]
            ],
            indent=2,
            ensure_ascii=False,
        )[:5000]
        params_json = json.dumps(
            [{"paramcd": p.paramcd, "parameter": p.parameter} for p in params[:30]],
            indent=2,
            ensure_ascii=False,
        )[:3000]

        prompt = TEMPLATE_GOLD_BATCH.format(
            num_deliverables=len(deliverables),
            deliverables_json=deliverables_json,
            vars_json=vars_json,
            params_json=params_json,
        )

        print(f"    Prompt size: {len(prompt)} chars")

        class GoldBatchResponse(BaseModel):
            deliverables: List[dict]

        result = self.run(prompt, result_type=GoldBatchResponse)

        specs = []
        if result and hasattr(result, "deliverables"):
            for item in result.deliverables:
                try:
                    platinum_data = (
                        item.get("platinum", {}) if isinstance(item, dict) else {}
                    )
                    gold_data = (
                        item.get("gold_statistics", [])
                        if isinstance(item, dict)
                        else []
                    )

                    spec = GeneratedSpec(
                        platinum=(
                            [PlatinumDeliverableSpec(**platinum_data)]
                            if platinum_data
                            else []
                        ),
                        gold_statistics=[
                            GoldStatisticSpec(**gs)
                            for gs in gold_data
                            if isinstance(gs, dict)
                        ],
                        confidence_notes=(
                            item.get("confidence_notes", [])
                            if isinstance(item, dict)
                            else []
                        ),
                    )
                    specs.append(spec)
                except Exception as e:
                    print(f"    Warning: Could not parse deliverable: {e}")
                    specs.append(GeneratedSpec())

        while len(specs) < len(deliverables):
            specs.append(GeneratedSpec())

        return specs

    def generate_for_context(
        self, context: MockShellContext, deliverable_ids: Optional[List[str]] = None
    ) -> List[GeneratedSpec]:
        """Generate specs with optimized two-phase approach."""
        deliverables = context.deliverables
        if deliverable_ids:
            deliverables = [
                d for d in deliverables if d.deliverable_id in deliverable_ids
            ]

        print(f"Phase 1: Extracting elements from {len(deliverables)} deliverables...")
        elements = self.extract_all_elements(
            MockShellContext(
                study_title=context.study_title,
                protocol_no=context.protocol_no,
                deliverables=deliverables,
            )
        )
        print(f"  Found {len(elements)} unique elements")

        print("Phase 1: Generating all variables in batch...")
        spec = self.generate_variables_batch(
            elements,
            protocol_no=context.protocol_no,
            study_title=context.study_title,
        )
        print(
            f"  Generated {len(spec.silver_variables)} silver variables, "
            f"{len(spec.params)} params"
        )

        print("Phase 2: Generating gold statistics in batches...")

        specs = []
        batch_size = 5

        for i in range(0, len(deliverables), batch_size):
            batch = deliverables[i : i + batch_size]
            print(f"  Batch {i // batch_size + 1}: {len(batch)} deliverables...")

            batch_specs = self.generate_gold_batch(
                batch, spec.silver_variables, spec.params
            )

            for j, batch_spec in enumerate(batch_specs):
                if j < len(batch):
                    specs.append(batch_spec)

        if specs:
            specs[0].silver_variables = spec.silver_variables
            specs[0].params = spec.params
            specs[0].confidence_notes.extend(spec.confidence_notes)

        return specs

    def debug_deliverable(
        self, context: MockShellContext, deliverable_id: str, verbose: bool = False
    ) -> GeneratedSpec:
        """Debug a single deliverable with detailed output."""
        deliverable = None
        for d in context.deliverables:
            if d.deliverable_id == deliverable_id:
                deliverable = d
                break

        if not deliverable:
            print(f"Deliverable not found: {deliverable_id}")
            return GeneratedSpec()

        if verbose:
            print(f"\nDebugging: {deliverable_id}")
            print(f"  Type: {deliverable.deliverable_type}")
            print(f"  Title: {deliverable.title}")
            print(f"  Population: {deliverable.population}")
            if deliverable.table_data:
                print(f"  Table rows: {len(deliverable.table_data)}")

        elements = self.extract_all_elements(
            MockShellContext(
                study_title=context.study_title,
                protocol_no=context.protocol_no,
                deliverables=[deliverable],
            )
        )

        if verbose:
            print(f"\n  Extracted {len(elements)} elements:")
            for key, elem in list(elements.items())[:10]:
                print(f"    - {elem.label} ({elem.element_type})")

        spec = self.generate_variables_batch(
            elements,
            protocol_no=context.protocol_no,
            study_title=context.study_title,
        )

        if verbose:
            print(f"\n  Generated {len(spec.silver_variables)} variables:")
            for v in spec.silver_variables[:5]:
                print(f"    - {v.var_name}: {v.var_label}")

        return spec


SpecGenerator = MetaGenerator
