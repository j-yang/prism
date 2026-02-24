"""Memory Store for Spec Agent.

Stores learned patterns in DuckDB for cross-study learning.
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, List

import duckdb


@dataclass
class Pattern:
    """A learned pattern from human corrections."""

    pattern_id: str
    pattern_type: str  # 'naming', 'derivation', 'selection', 'statistics'
    input_pattern: str  # What triggered this (e.g., "Any AE related to CART")
    output_spec: dict  # The correct output specification
    rule: str  # Human-readable rule
    source_study: str
    verified: bool = True
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


CREATE_MEMORY_SCHEMA = """
CREATE TABLE IF NOT EXISTS patterns (
    pattern_id VARCHAR PRIMARY KEY,
    pattern_type VARCHAR NOT NULL,
    input_pattern VARCHAR NOT NULL,
    output_spec JSON,
    rule VARCHAR,
    source_study VARCHAR,
    verified BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS variable_mappings (
    var_name VARCHAR PRIMARY KEY,
    als_field VARCHAR,
    derivation VARCHAR,
    label VARCHAR,
    schema_type VARCHAR,
    first_seen_study VARCHAR,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS study_history (
    study_id VARCHAR PRIMARY KEY,
    spec_file VARCHAR,
    generated_at TIMESTAMP,
    reviewed_at TIMESTAMP,
    patterns_learned INTEGER DEFAULT 0
);
"""


class MemoryStore:
    """DuckDB-based memory store for learned patterns."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            home = Path.home()
            prism_dir = home / ".prism"
            prism_dir.mkdir(exist_ok=True)
            db_path = str(prism_dir / "memory.duckdb")

        self.db_path = db_path
        self._conn = None

    @property
    def conn(self) -> duckdb.DuckDBPyConnection:
        if self._conn is None:
            self._conn = duckdb.connect(self.db_path)
            self._init_schema()
        return self._conn

    def _init_schema(self):
        """Initialize database schema."""
        self._conn.execute(CREATE_MEMORY_SCHEMA)

    def close(self):
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def add_pattern(self, pattern: Pattern) -> bool:
        """Add a new learned pattern."""
        try:
            self.conn.execute(
                """
                INSERT OR REPLACE INTO patterns 
                (pattern_id, pattern_type, input_pattern, output_spec, rule, source_study, verified, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                [
                    pattern.pattern_id,
                    pattern.pattern_type,
                    pattern.input_pattern,
                    json.dumps(pattern.output_spec),
                    pattern.rule,
                    pattern.source_study,
                    pattern.verified,
                    pattern.created_at,
                ],
            )
            return True
        except Exception as e:
            print(f"Error adding pattern: {e}")
            return False

    def get_patterns(self, pattern_type: Optional[str] = None) -> List[dict]:
        """Retrieve patterns, optionally filtered by type."""
        if pattern_type:
            result = self.conn.execute(
                """
                SELECT * FROM patterns WHERE pattern_type = ? ORDER BY created_at DESC
            """,
                [pattern_type],
            ).fetchall()
        else:
            result = self.conn.execute("""
                SELECT * FROM patterns ORDER BY created_at DESC
            """).fetchall()

        columns = [
            "pattern_id",
            "pattern_type",
            "input_pattern",
            "output_spec",
            "rule",
            "source_study",
            "verified",
            "created_at",
        ]
        return [dict(zip(columns, row)) for row in result]

    def find_matching_pattern(
        self, input_text: str, pattern_type: Optional[str] = None
    ) -> Optional[dict]:
        """Find a pattern that matches the input text."""
        input_lower = input_text.lower()

        patterns = self.get_patterns(pattern_type)

        for pattern in patterns:
            if pattern["input_pattern"].lower() in input_lower:
                return pattern

        return None

    def get_patterns_for_prompt(self, limit: int = 20) -> str:
        """Get patterns formatted for LLM prompt."""
        patterns = self.get_patterns()[:limit]

        if not patterns:
            return "[]"

        simplified = []
        for p in patterns:
            simplified.append(
                {
                    "type": p["pattern_type"],
                    "input": p["input_pattern"],
                    "output": json.loads(p["output_spec"])
                    if isinstance(p["output_spec"], str)
                    else p["output_spec"],
                    "rule": p["rule"],
                }
            )

        return json.dumps(simplified, indent=2, ensure_ascii=False)

    def save_variable_mapping(
        self,
        var_name: str,
        als_field: str,
        derivation: str,
        label: str,
        schema_type: str,
        study_id: str,
    ):
        """Save a variable mapping for reuse."""
        self.conn.execute(
            """
            INSERT OR REPLACE INTO variable_mappings 
            (var_name, als_field, derivation, label, schema_type, first_seen_study, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
            [var_name, als_field, derivation, label, schema_type, study_id],
        )

    def get_variable_mapping(self, var_name: str) -> Optional[dict]:
        """Get a previously saved variable mapping."""
        result = self.conn.execute(
            """
            SELECT var_name, als_field, derivation, label, schema_type 
            FROM variable_mappings WHERE var_name = ?
        """,
            [var_name],
        ).fetchone()

        if result:
            return {
                "var_name": result[0],
                "als_field": result[1],
                "derivation": result[2],
                "label": result[3],
                "schema_type": result[4],
            }
        return None

    def record_study(self, study_id: str, spec_file: str, patterns_learned: int = 0):
        """Record study processing history."""
        self.conn.execute(
            """
            INSERT OR REPLACE INTO study_history 
            (study_id, spec_file, generated_at, patterns_learned)
            VALUES (?, ?, CURRENT_TIMESTAMP, ?)
        """,
            [study_id, spec_file, patterns_learned],
        )

    def mark_study_reviewed(self, study_id: str):
        """Mark a study spec as reviewed."""
        self.conn.execute(
            """
            UPDATE study_history SET reviewed_at = CURRENT_TIMESTAMP 
            WHERE study_id = ?
        """,
            [study_id],
        )

    def get_stats(self) -> dict:
        """Get memory store statistics."""
        pattern_count = self.conn.execute("SELECT COUNT(*) FROM patterns").fetchone()[0]
        var_count = self.conn.execute(
            "SELECT COUNT(*) FROM variable_mappings"
        ).fetchone()[0]
        study_count = self.conn.execute(
            "SELECT COUNT(*) FROM study_history"
        ).fetchone()[0]

        return {
            "patterns": pattern_count,
            "variable_mappings": var_count,
            "studies": study_count,
            "db_path": self.db_path,
        }

    def clear_all(self):
        """Clear all stored data (use with caution)."""
        self.conn.execute("DELETE FROM patterns")
        self.conn.execute("DELETE FROM variable_mappings")
        self.conn.execute("DELETE FROM study_history")


_memory_store: Optional[MemoryStore] = None


def get_memory_store(db_path: Optional[str] = None) -> MemoryStore:
    """Get or create the global memory store instance."""
    global _memory_store
    if _memory_store is None:
        _memory_store = MemoryStore(db_path)
    return _memory_store
