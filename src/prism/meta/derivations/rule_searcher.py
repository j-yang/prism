"""Derivation Rule Searcher.

Searches for derivation rules from Mock Shell notes and footnotes.
"""

import logging
from typing import List, Set

from prism.meta.extractor import Deliverable, MockShellContext

logger = logging.getLogger(__name__)


class DerivationRuleSearcher:
    """Search derivation rules from Mock Shell and SAP documents."""

    def __init__(self, mock_context: MockShellContext, cache_db=None):
        """Initialize searcher.

        Args:
            mock_context: Extracted mock shell context
            cache_db: Optional cache database path
        """
        self.mock_context = mock_context
        self.cache_db = cache_db

    def search_mock_notes(self, keywords: List[str]) -> List[str]:
        """Search Mock Shell programming notes and footnotes.

        Args:
            keywords: List of keywords to search

        Returns:
            List of matching rules/notes
        """
        rules = []
        keywords_lower = {kw.lower() for kw in keywords}

        for note in self.mock_context.all_programming_notes:
            if self._matches_keywords(note, keywords_lower):
                rules.append(f"[Mock Shell] {note}")

        for key, footnote in self.mock_context.all_footnotes.items():
            if self._matches_keywords(footnote, keywords_lower):
                rules.append(f"[Mock Shell Footnote {key}] {footnote}")

        for deliverable in self.mock_context.deliverables:
            if self._is_relevant_deliverable(deliverable, keywords_lower):
                for note in deliverable.programming_notes:
                    if self._matches_keywords(note, keywords_lower):
                        rules.append(f"[{deliverable.deliverable_id}] {note}")

                for key, footnote in deliverable.footnotes.items():
                    if self._matches_keywords(footnote, keywords_lower):
                        rules.append(
                            f"[{deliverable.deliverable_id} Footnote {key}] {footnote}"
                        )

        return rules

    def _matches_keywords(self, text: str, keywords: Set[str]) -> bool:
        """Check if text matches any keyword.

        Args:
            text: Text to check
            keywords: Set of lowercase keywords

        Returns:
            True if any keyword matches
        """
        if not keywords:
            return False

        text_lower = text.lower()
        return any(kw in text_lower for kw in keywords)

    def _is_relevant_deliverable(
        self, deliverable: Deliverable, keywords: Set[str]
    ) -> bool:
        """Check if deliverable is relevant to keywords.

        Args:
            deliverable: Deliverable to check
            keywords: Set of lowercase keywords

        Returns:
            True if deliverable is relevant
        """
        text = (
            f"{deliverable.title} "
            f"{' '.join(deliverable.columns)} "
            f"{' '.join(deliverable.rows)}"
        )
        return self._matches_keywords(text, keywords)
