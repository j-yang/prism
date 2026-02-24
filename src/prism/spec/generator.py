"""Spec Generator.

Generates clinical trial specifications using LLM.
"""

import json
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, List, Dict

from prism.agent import call_deepseek
from prism.spec.extractor import MockShellContext, Deliverable
from prism.spec.matcher import load_als_dict
from prism.spec.memory import get_memory_store
from prism.spec.templates import (
    format_prompt,
    TEMPLATE_GENERATE_SPEC,
    TEMPLATE_BATCH_VARIABLES,
)


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


@dataclass
class ExtractedElement:
    """An element extracted from mock shell."""

    label: str
    element_type: str
    deliverable_ids: List[str] = field(default_factory=list)
    context: str = ""


class SpecGenerator:
    """Generate specifications using LLM."""

    def __init__(self, als_path: Optional[str] = None, memory_db: Optional[str] = None):
        self.als_dict = load_als_dict(als_path) if als_path else {}
        self.memory = get_memory_store(memory_db)

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

    def generate_variables_batch(
        self,
        elements: Dict[str, ExtractedElement],
        protocol_no: str = "",
        study_title: str = "",
    ) -> tuple:
        """Generate all silver variables and params in one LLM call."""
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

        elements_json = json.dumps(elements_list[:100], indent=2, ensure_ascii=False)[
            :8000
        ]
        als_vars_json = json.dumps(
            list(self.als_dict.values())[:150], indent=2, ensure_ascii=False
        )[:6000]
        patterns_json = self.memory.get_patterns_for_prompt(limit=20)

        prompt = format_prompt(
            TEMPLATE_BATCH_VARIABLES,
            protocol_no=protocol_no,
            study_title=study_title,
            elements_json=elements_json,
            als_vars_json=als_vars_json,
            patterns_json=patterns_json,
        )

        response = call_deepseek(prompt, temperature=0.2, timeout=120)

        if response:
            parsed = self._parse_response(response)
            if not parsed.get("silver_variables"):
                print(
                    f"DEBUG: LLM response parsed but no silver_variables. Response preview: {response[:500]}"
                )
                print(f"DEBUG: Parsed keys: {list(parsed.keys())}")
            return (
                parsed.get("silver_variables", []),
                parsed.get("params", []),
                parsed.get("study_config", {}),
                parsed.get("confidence_notes", []),
            )
        else:
            print("DEBUG: LLM returned empty response")

        return [], [], {}, []

    def generate_gold_batch(
        self,
        deliverables: List[Deliverable],
        silver_variables: List[dict],
        params: List[dict],
    ) -> List[tuple]:
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

        vars_json = json.dumps(silver_variables[:50], indent=2, ensure_ascii=False)[
            :5000
        ]
        params_json = json.dumps(params[:30], indent=2, ensure_ascii=False)[:3000]

        prompt = f"""## Task: Generate Gold Statistics for Multiple Deliverables

### Deliverables ({len(deliverables)} items)
```json
{deliverables_json}
```

### Available Silver Variables
```json
{vars_json}
```

### Available Parameters
```json
{params_json}
```

### Your Tasks

For EACH deliverable, generate:
1. **platinum** definition
2. **gold_statistics** for each row/column

Return JSON array with one entry per deliverable:
```json
[
  {{
    "deliverable_id": "14.1.1",
    "platinum": {{
      "deliverable_id": "14.1.1",
      "deliverable_type": "listing",
      "title": "...",
      "population": "...",
      "schema": "baseline"
    }},
    "gold_statistics": [
      {{
        "deliverable_id": "14.1.1",
        "row_label": "Age",
        "element_type": "variable",
        "element_id": "age",
        "selection": "",
        "statistics": {{"value": "raw"}},
        "group_by": []
      }}
    ],
    "confidence_notes": []
  }}
]
```

Rules:
- For listings: statistics = {{"value": "raw"}}
- For tables: statistics = {{"n": "count", "pct": "percent"}}
- For figures: statistics = {{"mean": "avg", "sd": "std"}}
- Use element_id from available silver variables
- element_type: "variable", "param", or "flag"

Return ONLY valid JSON array.
"""

        response = call_deepseek(prompt, temperature=0.2, timeout=120)

        results = []
        if response:
            parsed = self._parse_response(response)
            if isinstance(parsed, list):
                for item in parsed:
                    results.append(
                        (
                            item.get("gold_statistics", []),
                            item.get("platinum", {}),
                            item.get("confidence_notes", []),
                        )
                    )

        while len(results) < len(deliverables):
            results.append(([], {}, []))

        return results

    def generate_for_context_optimized(
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
        silver_variables, params, study_config, batch_notes = (
            self.generate_variables_batch(
                elements,
                protocol_no=context.protocol_no,
                study_title=context.study_title,
            )
        )
        print(
            f"  Generated {len(silver_variables)} silver variables, {len(params)} params"
        )

        print(f"Phase 2: Generating gold statistics in batches...")

        specs = []
        batch_size = 10

        for i in range(0, len(deliverables), batch_size):
            batch = deliverables[i : i + batch_size]
            print(f"  Batch {i // batch_size + 1}: {len(batch)} deliverables...")

            results = self.generate_gold_batch(batch, silver_variables, params)

            for j, (gold_stats, platinum_def, gold_notes) in enumerate(results):
                if j < len(batch):
                    spec = GeneratedSpec(
                        deliverable_id=batch[j].deliverable_id,
                        platinum=platinum_def,
                        silver_variables=[],
                        gold_statistics=gold_stats,
                        params=[],
                        study_config={},
                        confidence_notes=gold_notes,
                    )
                    specs.append(spec)

        if specs:
            specs[0].silver_variables = silver_variables
            specs[0].params = params
            specs[0].study_config = study_config
            if batch_notes:
                specs[0].confidence_notes.extend(batch_notes)

        return specs

    def generate_for_deliverable(
        self, deliverable: Deliverable, protocol_no: str = "", study_title: str = ""
    ) -> GeneratedSpec:
        """Generate spec for a single deliverable (legacy method)."""
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
        """Generate specs for multiple deliverables (legacy method)."""
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
        except json.JSONDecodeError:
            pass

        start = response.find("{")
        end = response.rfind("}")

        if start != -1 and end != -1:
            try:
                return json.loads(response[start : end + 1])
            except json.JSONDecodeError:
                pass

        start = response.find("[")
        end = response.rfind("]")

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
    optimized: bool = True,
) -> List[GeneratedSpec]:
    """Convenience function to generate specs."""
    from prism.spec.extractor import extract_mock_shell

    context = extract_mock_shell(mock_shell_path)
    generator = SpecGenerator(als_path, memory_db)

    if optimized:
        specs = generator.generate_for_context_optimized(context, deliverable_ids)
    else:
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
