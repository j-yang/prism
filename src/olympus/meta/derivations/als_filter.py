"""ALS Field Filter.

Intelligently filters ALS fields based on variable requirements.
"""

import logging
from typing import Dict, List, Set

logger = logging.getLogger(__name__)


class ALSFilter:
    """Filter ALS fields based on keywords from variable requirements."""

    STOP_WORDS = {
        "of",
        "the",
        "a",
        "an",
        "in",
        "to",
        "for",
        "or",
        "and",
        "by",
        "with",
        "from",
        "on",
        "at",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
    }

    DOMAIN_KEYWORDS = {
        "ae": ["ae", "adverse", "event", "sae", "serious"],
        "dm": ["age", "sex", "race", "birth", "demographic", "subject"],
        "ex": ["exposure", "dose", "treatment", "infusion", "drug"],
        "lb": ["lab", "laboratory", "test", "blood", "urine"],
        "vs": ["vital", "sign", "blood pressure", "heart rate", "temperature"],
        "cm": ["conmed", "medication", "drug", "concomitant"],
        "mh": ["medical", "history", "disease", "condition"],
    }

    def __init__(self, als_dict: Dict, max_fields: int = 100):
        """Initialize ALS filter.

        Args:
            als_dict: Dictionary of ALS fields (field_oid -> info)
            max_fields: Maximum number of fields to return
        """
        self.als_dict = als_dict
        self.max_fields = max_fields

    def filter_for_requirements(self, requirements: List[Dict]) -> List[Dict]:
        """Filter ALS fields relevant to variable requirements.

        Args:
            requirements: List of variable requirements
                Each requirement should have:
                - var_name: Variable name (snake_case)
                - var_label: Variable label
                - schema: Schema type (baseline/occurrence/longitudinal)

        Returns:
            List of relevant ALS field info dictionaries
        """
        all_keywords = set()
        for req in requirements:
            keywords = self.extract_keywords(req)
            all_keywords.update(keywords)

        relevant_fields = []
        for field_oid, info in self.als_dict.items():
            score = self.score_als_field(info, all_keywords)
            if score > 0:
                relevant_fields.append({**info, "score": score})

        relevant_fields.sort(key=lambda x: x["score"], reverse=True)
        return relevant_fields[: self.max_fields]

    def extract_keywords(self, requirement: Dict) -> Set[str]:
        """Extract search keywords from variable requirement.

        Args:
            requirement: Variable requirement dict

        Returns:
            Set of lowercase keywords
        """
        keywords = set()

        var_name = requirement.get("var_name", "")
        if var_name:
            words = var_name.split("_")
            keywords.update(w.lower() for w in words if w and len(w) > 1)

        var_label = requirement.get("var_label", "")
        if var_label:
            words = var_label.lower().split()
            keywords.update(w for w in words if w not in self.STOP_WORDS and len(w) > 1)

        schema = requirement.get("schema", "")
        if schema:
            schema_domains = self._infer_domains_from_schema(schema)
            keywords.update(schema_domains)

        label_lower = var_label.lower()
        for domain, domain_kws in self.DOMAIN_KEYWORDS.items():
            if any(kw in label_lower for kw in domain_kws):
                keywords.add(domain.upper())

        return keywords

    def _infer_domains_from_schema(self, schema: str) -> Set[str]:
        """Infer likely domains from schema type.

        Args:
            schema: Schema type (baseline/occurrence/longitudinal)

        Returns:
            Set of likely domain codes
        """
        schema_domain_map = {
            "baseline": {"DM", "IE", "MH", "VS"},
            "occurrence": {"AE", "CM", "EX", "LB"},
            "longitudinal": {"VS", "LB", "RS"},
        }
        return schema_domain_map.get(schema, set())

    def score_als_field(self, field_info: Dict, keywords: Set[str]) -> int:
        """Score ALS field relevance to keywords.

        Args:
            field_info: ALS field info dict
            keywords: Set of lowercase keywords

        Returns:
            Relevance score (0 = not relevant)
        """
        score = 0

        field_oid = field_info.get("field_oid", "").lower()
        label = field_info.get("label", "").lower()
        domain = field_info.get("domain", "").lower()

        for kw in keywords:
            kw_lower = kw.lower()

            if kw_lower == field_oid:
                score += 10

            if kw_lower in label:
                score += 5

            if kw_lower == domain:
                score += 3

        return score
