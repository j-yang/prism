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
from prism.core.cache import CacheManager
from prism.core.models import (
    GeneratedSpec,
    GoldStatisticSpec,
    ParamSpec,
    PlatinumDeliverableSpec,
    SilverVariableSpec,
)
from prism.meta.als_filter import ALSFilter
from prism.meta.extractor import Deliverable, MockShellContext
from prism.meta.rule_searcher import DerivationRuleSearcher
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
        mock_context: Optional[MockShellContext] = None,
        cache_db: Optional[str] = None,
    ):
        super().__init__(provider=provider, db_path=db_path, als_path=als_path)
        self.tools.load_als_dict(als_path)

        self.mock_context = mock_context
        self.cache = CacheManager(cache_db)

        if mock_context:
            self.rule_searcher = DerivationRuleSearcher(mock_context, self.cache)
        else:
            self.rule_searcher = None

        if self.tools._als_dict:
            self.als_filter = ALSFilter(self.tools._als_dict)
        else:
            self.als_filter = None

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
        """Generate all silver variables and params in multiple LLM calls.

        Two-phase approach:
        1. Analyze elements → generate variable requirements (no ALS needed)
        2. Search rules + filter ALS + generate code
        """
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

        all_silver_vars = []
        all_params = []
        all_notes = []

        batch_size = 10
        for i in range(0, len(elements_list), batch_size):
            batch = elements_list[i : i + batch_size]

            # Phase 1: Generate variable requirements (no ALS needed)
            requirements = self._generate_requirements_batch(batch)

            # Phase 2: Search rules + filter ALS + generate code
            if requirements:
                result = self._derive_variables_batch(
                    requirements, protocol_no, study_title
                )

                if result:
                    all_silver_vars.extend(result.silver_variables)
                    all_params.extend(result.params)
                    all_notes.extend(result.confidence_notes)
                    print(
                        f"  Batch {i // batch_size + 1}: "
                        f"Generated {len(result.silver_variables)} variables"
                    )
                else:
                    print("    No response or validation failed")

        return GeneratedSpec(
            silver_variables=all_silver_vars,
            params=all_params,
            confidence_notes=all_notes,
        )

    def _generate_requirements_batch(self, batch: List[Dict]) -> List[Dict]:
        """Phase 1: Generate variable requirements using rules (no LLM, no ALS).
        
        Args:
            batch: List of elements
            
        Returns:
            List of variable requirements
        """
        requirements = []
        for elem in batch:
            label = elem.get("label", "")
            req = {
                "var_name": self._to_snake_case(label),
                "var_label": self._clean_label(label),
                "schema": self._infer_schema(elem),
                "data_type": self._infer_data_type(label),
                "description": elem.get("context", ""),
                "element_type": elem.get("type", ""),
                "used_in": elem.get("used_in", []),
            }
            requirements.append(req)
        return requirements
    
    def _to_snake_case(self, label: str) -> str:
        """Convert label to snake_case."""
        label = re.sub(r"\[([a-z])\]", "", label)
        label = label.lower()
        label = re.sub(r"[^a-z0-9]+", "_", label)
        label = label.strip("_")
        return label
    
    def _clean_label(self, label: str) -> str:
        """Clean label by removing footnote markers."""
        return re.sub(r"\[([a-z])\]", "", label).strip()
    
    def _infer_schema(self, elem: Dict) -> str:
        """Infer schema from element content."""
        label = elem.get("label", "").lower()
        context = elem.get("context", "").lower()
        
        if any(kw in label for kw in ["ae", "adverse", "sae", "medication", "conmed", "cm"]):
            return "occurrence"
        elif any(kw in label for kw in ["visit", "over time", "longitudinal", "by visit"]):
            return "longitudinal"
        elif any(kw in context for kw in ["listing"]):
            if any(kw in label for kw in ["ae", "adverse", "medication"]):
                return "occurrence"
            return "baseline"
        else:
            return "baseline"
    
    def _infer_data_type(self, label: str) -> str:
        """Infer data type from label."""
        label_lower = label.lower()
        
        if any(kw in label_lower for kw in ["date", "dtc", "datetime"]):
            return "DATE"
        elif any(kw in label_lower for kw in ["age", "count", "number", "n", "no."]):
            if "age" in label_lower and "range" not in label_lower:
                return "INTEGER"
            return "TEXT"
        elif any(kw in label_lower for kw in ["score", "value", "duration", "days", "months", "years"]):
            if "duration" in label_lower or "days" in label_lower:
                return "INTEGER"
            return "FLOAT"
        else:
            return "TEXT"

    def _derive_variables_batch(
        self, requirements: List[Dict], protocol_no: str, study_title: str
    ) -> Optional[GeneratedSpec]:
        """Phase 2: Derive variables with rules and ALS mapping.

        Args:
            requirements: List of variable requirements
            protocol_no: Protocol number
            study_title: Study title

        Returns:
            GeneratedSpec with silver_variables
        """
        # Search for derivation rules
        all_keywords = set()
        for req in requirements:
            keywords = (
                self.als_filter.extract_keywords(req) if self.als_filter else set()
            )
            all_keywords.update(keywords)

        derivation_rules = []
        if self.rule_searcher and all_keywords:
            derivation_rules = self.rule_searcher.search_mock_notes(list(all_keywords))

        # Filter ALS fields
        if self.als_filter:
            relevant_als = self.als_filter.filter_for_requirements(requirements)
            als_vars_json = json.dumps(relevant_als, indent=2, ensure_ascii=False)
            als_count = len(relevant_als)
            total_count = len(self.tools._als_dict)
            reduction = 100 * (1 - als_count / total_count) if total_count > 0 else 0
            print(
                f"    ALS filtering: {als_count}/{total_count} fields "
                f"({reduction:.1f}% reduction)"
            )
        else:
            als_vars_json = json.dumps(
                list(self.tools._als_dict.values()), indent=2, ensure_ascii=False
            )

        # Build prompt
        requirements_json = json.dumps(requirements, indent=2, ensure_ascii=False)
        rules_json = json.dumps(derivation_rules[:5], indent=2, ensure_ascii=False)

        prompt = f"""## Task: Generate Silver Variables with ALS Mapping

### Study Information
- Protocol: {protocol_no}
- Title: {study_title}

### Variable Requirements
```json
{requirements_json}
```

### Derivation Rules (from Mock Shell)
```json
{rules_json}
```

### Available ALS Fields
```json
{als_vars_json}
```

---

## Output Schema

Generate JSON with this structure:

```json
{{
  "silver_variables": [
    {{
      "var_name": "snake_case_name",
      "var_label": "Human readable label",
      "schema": "baseline|occurrence|longitudinal",
      "data_type": "TEXT|INTEGER|FLOAT|DATE",
      "source_vars": "DM.AGE, DM.SEX",
      "transformation": "Python code or empty",
      "transformation_type": "direct|python",
      "param_ref": "",
      "description": "",
      "confidence": "high|medium|low"
    }}
  ],
  "params": [
    {{
      "paramcd": "CODE",
      "parameter": "Full parameter name",
      "category": "Efficacy|Safety|PK|PD",
      "unit": "unit",
      "default_source_form": "",
      "default_source_var": ""
    }}
  ],
  "confidence_notes": ["Items needing review"]
}}
```

## Instructions

1. For each variable requirement, find the best ALS field mapping
2. Use derivation rules if available (prioritize Mock Shell rules)
3. Generate Polars transformation code if needed
4. Set confidence level based on mapping quality

Output ONLY valid JSON, no markdown.
"""

        result = self.run(prompt, result_type=GeneratedSpec)
        return result

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
