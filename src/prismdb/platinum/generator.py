"""
PRISM-DB Platinum Layer Generator

Generate Data Review Portal (single HTML with DuckDB WASM).
"""

import os
import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from ..database import Database


class PlatinumGenerator:
    """
    Generate Data Review Portal for study data review.

    Output:
        - index.html
        - app.js
        - style.css
        - study.duckdb (copied)
    """

    def __init__(self, db: Database):
        self.db = db
        self.static_dir = Path(__file__).parent / "static"

    def generate(
        self, output_dir: str = "generated/platinum", db_path: Optional[str] = None
    ) -> Dict:
        """
        Generate the Data Review Portal.

        Args:
            output_dir: Output directory
            db_path: Path to study.duckdb (if different from current db)

        Returns:
            Dict with generation info
        """
        os.makedirs(output_dir, exist_ok=True)

        # Copy static files
        for filename in ["index.html", "style.css", "app.js"]:
            src = self.static_dir / filename
            dst = Path(output_dir) / filename
            shutil.copy(src, dst)

        # Copy database file
        if db_path:
            db_dst = Path(output_dir) / "study.duckdb"
            shutil.copy(db_path, db_dst)

        # Generate manifest
        manifest = {
            "generated_at": datetime.now().isoformat(),
            "files": ["index.html", "style.css", "app.js", "study.duckdb"],
        }

        manifest_path = Path(output_dir) / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        return {
            "output_dir": output_dir,
            "files": manifest["files"],
            "generated_at": manifest["generated_at"],
        }
