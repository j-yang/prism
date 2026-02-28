"""Shared PydanticAI agent infrastructure.

Provides base agent class with common tools for all PRISM agents.
"""

import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

try:
    from dotenv import load_dotenv

    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass


class ToolRegistry:
    """Registry for shared tools available to all agents."""

    def __init__(self, db_path: Optional[str] = None, als_path: Optional[str] = None):
        self.db_path = db_path
        self.als_path = als_path
        self._als_dict: dict = {}

    def load_als_dict(self, als_path: Optional[str] = None) -> dict:
        """Load ALS dictionary from Excel file.

        Args:
            als_path: Path to ALS Excel file

        Returns:
            Dictionary mapping FieldOID to field info
        """
        import pandas as pd

        path = als_path or self.als_path
        if not path:
            return {}

        if self._als_dict and als_path is None:
            return self._als_dict

        try:
            df = pd.read_excel(path, sheet_name="Fields")
            for _, row in df.iterrows():
                field_oid = row.get("FieldOID") or row.get("field_oid")
                if pd.notna(field_oid):
                    label = (
                        row.get("FieldLabel")
                        or row.get("field_label")
                        or row.get("DraftFieldName")
                        or row.get("SASLabel")
                        or ""
                    )

                    form_oid = row.get("FormOID") or row.get("form_oid") or ""
                    domain = (
                        row.get("Domain")
                        or row.get("domain")
                        or (
                            form_oid.split(".")[0] if "." in str(form_oid) else form_oid
                        )
                        or ""
                    )

                    data_type = (
                        row.get("DataType")
                        or row.get("data_type")
                        or row.get("DataFormat")
                        or ""
                    )

                    self._als_dict[field_oid] = {
                        "field_oid": field_oid,
                        "label": str(label) if pd.notna(label) else "",
                        "domain": str(domain).upper() if domain else "",
                        "data_type": str(data_type) if pd.notna(data_type) else "",
                    }
            logger.info(f"Loaded {len(self._als_dict)} ALS fields")
        except Exception as e:
            logger.warning(f"Could not load ALS dict: {e}")

        return self._als_dict

    def lookup_als(
        self, domain: Optional[str] = None, keywords: Optional[list[str]] = None
    ) -> list[dict]:
        """Look up ALS fields by domain and/or keywords.

        Args:
            domain: Filter by domain (e.g., "DM", "AE", "EX")
            keywords: Filter by keywords in label

        Returns:
            List of matching field info dictionaries
        """
        als_dict = self.load_als_dict()
        results = []

        for field_oid, info in als_dict.items():
            if domain:
                if info.get("domain", "").upper() != domain.upper():
                    continue

            if keywords:
                label = info.get("label", "").lower()
                if not any(kw.lower() in label for kw in keywords):
                    continue

            results.append(info)

        return results

    def get_bronze_schema(self, db_path: Optional[str] = None) -> dict[str, list[str]]:
        """Get available Bronze layer tables and columns.

        Args:
            db_path: Path to DuckDB database

        Returns:
            Dictionary mapping table name to list of column names
        """
        import duckdb

        path = db_path or self.db_path
        if not path or not Path(path).exists():
            return {}

        try:
            con = duckdb.connect(path, read_only=True)

            tables = con.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'bronze'"
            ).fetchall()

            schema = {}
            for (table_name,) in tables:
                columns = con.execute(
                    f"SELECT column_name FROM information_schema.columns "
                    f"WHERE table_schema = 'bronze' AND table_name = '{table_name}'"
                ).fetchall()
                schema[f"bronze.{table_name}"] = [col[0] for col in columns]

            con.close()
            return schema

        except Exception as e:
            logger.warning(f"Could not get bronze schema: {e}")
            return {}

    def get_meta_variables(
        self, schema: str, db_path: Optional[str] = None
    ) -> list[dict]:
        """Get variables from meta.silver_dictionary for a schema.

        Args:
            schema: Schema name (baseline, longitudinal, occurrence)
            db_path: Path to DuckDB database

        Returns:
            List of variable info dictionaries
        """
        import duckdb

        path = db_path or self.db_path
        if not path or not Path(path).exists():
            return []

        try:
            con = duckdb.connect(path, read_only=True)

            results = con.execute(
                "SELECT var_name, var_label, data_type, source_vars, transformation "
                "FROM meta.silver_dictionary WHERE schema = ?",
                [schema],
            ).fetchall()

            con.close()

            return [
                {
                    "var_name": row[0],
                    "var_label": row[1],
                    "data_type": row[2],
                    "source_vars": row[3],
                    "transformation": row[4],
                }
                for row in results
            ]

        except Exception as e:
            logger.warning(f"Could not get meta variables: {e}")
            return []

    def check_dependencies(
        self, var_names: list[str], db_path: Optional[str] = None
    ) -> dict[str, bool]:
        """Check if required variables exist in meta tables.

        Args:
            var_names: List of variable names to check
            db_path: Path to DuckDB database

        Returns:
            Dictionary mapping variable name to availability status
        """
        import duckdb

        path = db_path or self.db_path
        if not path or not Path(path).exists():
            return {name: False for name in var_names}

        try:
            con = duckdb.connect(path, read_only=True)

            placeholders = ",".join("?" * len(var_names))
            results = con.execute(
                f"SELECT var_name FROM meta.silver_dictionary "
                f"WHERE var_name IN ({placeholders})",
                var_names,
            ).fetchall()

            con.close()

            available = {row[0] for row in results}
            return {name: name in available for name in var_names}

        except Exception as e:
            logger.warning(f"Could not check dependencies: {e}")
            return {name: False for name in var_names}


class BaseAgent:
    """Base class for PRISM agents with shared functionality."""

    def __init__(
        self,
        provider: str = "deepseek",
        db_path: Optional[str] = None,
        als_path: Optional[str] = None,
    ):
        self.provider_name = provider
        self.db_path = db_path
        self.als_path = als_path
        self.tools = ToolRegistry(db_path=db_path, als_path=als_path)
        self._agent = None

    def _get_model_string(self) -> str:
        """Get model string for pydantic-ai based on provider."""
        if self.provider_name == "deepseek":
            return "deepseek:deepseek-chat"
        elif self.provider_name == "zhipu":
            return "zhipu:glm-4-flash"
        else:
            raise ValueError(f"Unknown provider: {self.provider_name}")

    def _get_system_prompt(self) -> str:
        """Get system prompt for the agent. Override in subclasses."""
        return "You are a helpful assistant."

    def create_agent(self, result_type: Any = None):
        """Create a pydantic-ai agent with configured settings.

        Args:
            result_type: Pydantic model for structured output

        Returns:
            Configured Agent instance
        """
        try:
            from pydantic_ai import Agent
        except ImportError:
            raise ImportError("pydantic-ai not installed. Run: uv add pydantic-ai")

        model = self._get_model_string()
        system_prompt = self._get_system_prompt()

        agent = Agent(
            model,
            system_prompt=system_prompt,
            result_type=result_type,
        )

        self._agent = agent
        return agent

    def run(self, prompt: str, result_type: Any = None) -> Any:
        """Run the agent with a prompt.

        Args:
            prompt: User prompt
            result_type: Pydantic model for structured output

        Returns:
            Agent result (structured if result_type provided)
        """
        if self._agent is None or result_type:
            self.create_agent(result_type)

        try:
            result = self._agent.run_sync(prompt)
            return result.data
        except Exception as e:
            logger.error(f"Agent run failed: {e}")
            raise
