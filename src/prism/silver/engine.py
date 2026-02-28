"""Silver Engine.

Generate and execute Python transformations for silver layer.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Template

from prism.core.database import Database
from prism.core.models import SilverVariableSpec
from prism.transforms import list_transforms

logger = logging.getLogger(__name__)


class SilverEngine:
    """Generate and execute silver transformations."""

    def __init__(self, db: Database):
        self.db = db

    def generate_transform_file(
        self,
        var: SilverVariableSpec,
        output_dir: str = "generated/transforms/silver",
    ) -> Optional[str]:
        """Generate Python transformation file for a variable.

        Args:
            var: Silver variable spec
            output_dir: Output directory

        Returns:
            Path to generated file or None if direct mapping
        """
        if var.transformation_type == "direct" or not var.transformation:
            return None

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        file_path = output_path / f"{var.var_name}.py"

        template = Template("""\"\"\"Derive {{ var_name }}.

{{ description|default("Silver variable derivation.", true) }}
\"\"\"

import polars as pl
from prism.transforms.registry import register_transform


@register_transform("{{ var_name }}")
def derive_{{ var_name }}(df: pl.DataFrame) -> pl.DataFrame:
    \"\"\"{{ var_label }}.\"\"\"
    return df.with_columns([
        {{ transformation }}
    ])
""")

        content = template.render(
            var_name=var.var_name,
            var_label=var.var_label,
            description=var.description,
            transformation=var.transformation,
        )

        file_path.write_text(content, encoding="utf-8")
        logger.info(f"Generated transform: {file_path}")
        return str(file_path)

    def generate_all_transforms(
        self,
        variables: List[SilverVariableSpec],
        output_dir: str = "generated/transforms/silver",
    ) -> Dict[str, str]:
        """Generate transformation files for all derived variables.

        Args:
            variables: List of silver variable specs
            output_dir: Output directory

        Returns:
            Dict mapping var_name to generated file path
        """
        results = {}
        for var in variables:
            path = self.generate_transform_file(var, output_dir)
            if path:
                results[var.var_name] = path
        return results

    def execute_transform(
        self,
        var_name: str,
        schema: str = "baseline",
        source_table: str = "bronze",
    ) -> bool:
        """Execute a registered transformation.

        Args:
            var_name: Variable name
            schema: Target schema (baseline/occurrence/longitudinal)
            source_table: Source bronze table

        Returns:
            True if successful
        """
        import polars as pl

        from prism.transforms import get_transform

        transform = get_transform(var_name)
        if not transform:
            logger.warning(f"Transform not found: {var_name}")
            return False

        source_df = self.db.query_df(f"SELECT * FROM {source_table}.{schema}")
        df = pl.from_pandas(source_df)

        result_df = transform(df)

        self.db.insert(f"silver.{schema}", result_df.to_pandas())

        logger.info(f"Executed transform: {var_name}")
        return True

    def execute_all_transforms(self, schema: str = "baseline") -> Dict[str, bool]:
        """Execute all registered transforms for a schema.

        Args:
            schema: Schema to process

        Returns:
            Dict mapping var_name to success status
        """
        results = {}
        for var_name in list_transforms():
            try:
                success = self.execute_transform(var_name, schema)
                results[var_name] = success
            except Exception as e:
                logger.error(f"Transform failed {var_name}: {e}")
                results[var_name] = False
        return results
