import json
import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from olympus.core.database import Database

logger = logging.getLogger(__name__)


def _deprecated_call_deepseek(prompt: str, **kwargs) -> str:
    """Deprecated: Use GoldAgent instead."""
    logger.warning("GoldEngine is deprecated. Use GoldAgent instead.")
    return ""


def _deprecated_extract_code_block(content: str, language: str) -> str:
    """Deprecated: Use GoldAgent instead."""
    return ""


class GoldEngine:
    TEMPLATES = {
        "demographics": {
            "pattern": r"(demog|demographics|baseline.*characteristics)",
            "description": "Demographics and Baseline Characteristics Table",
        },
        "ae_summary": {
            "pattern": r"(ae.*summary|adverse.*event.*summary|teae)",
            "description": "Adverse Events Summary Table",
        },
        "listing": {"pattern": r"(listing|list)", "description": "Data Listing"},
    }

    def __init__(self, db: Database, api_key: str = None):
        self.db = db
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        self.generation_log = {
            "generated_at": None,
            "stats": {"total": 0, "template": 0, "llm": 0, "skipped": 0},
            "outputs": [],
        }

    def generate_all(self, output_dir: str = "generated/analysis/") -> Dict[str, Any]:
        os.makedirs(output_dir, exist_ok=True)
        self.generation_log["generated_at"] = datetime.now().isoformat()

        outputs = self._load_outputs()

        for output in outputs:
            script = self._generate_single(output)
            if script:
                output_file = os.path.join(output_dir, f"{output['output_id']}.py")
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(script)
                logger.info(f"Generated: {output_file}")

        log_file = os.path.join(output_dir, "analysis_log.json")
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(self.generation_log, f, indent=2, ensure_ascii=False)

        return self.generation_log

    def _load_outputs(self) -> List[Dict]:
        sql = """
            SELECT 
                o.output_id,
                ANY_VALUE(o.output_type) AS output_type,
                ANY_VALUE(o.title) AS title,
                ANY_VALUE(o.schema) AS schema,
                ANY_VALUE(o.population) AS population,
                ANY_VALUE(o.section) AS section,
                ANY_VALUE(o.display_order) AS display_order,
                GROUP_CONCAT(ov.var_id) AS variable_ids
            FROM meta.outputs o
            LEFT JOIN meta.output_variables ov ON o.output_id = ov.output_id
            GROUP BY o.output_id
            ORDER BY
                ANY_VALUE(o.section) NULLS LAST,
                ANY_VALUE(o.display_order) NULLS LAST
        """
        df = self.db.query_df(sql)

        outputs = []
        for _, row in df.iterrows():
            output = row.to_dict()
            var_ids = output.get("variable_ids", "")
            if var_ids is None or (isinstance(var_ids, float) and pd.isna(var_ids)):
                output["variables"] = []
            elif isinstance(var_ids, str):
                output["variables"] = [v.strip() for v in var_ids.split(",")]
            else:
                output["variables"] = []
            outputs.append(output)

        return outputs

    def _generate_single(self, output: Dict) -> Optional[str]:
        output_id = output["output_id"]
        output_type = output.get("output_type", "table")
        schema = output.get("schema", "baseline")
        title = output.get("title", "")

        self.generation_log["stats"]["total"] += 1

        log_entry = {
            "output_id": output_id,
            "output_type": output_type,
            "schema": schema,
            "title": title,
            "method": None,
            "status": "success",
        }

        script = self._try_template(output)
        if script:
            log_entry["method"] = "template"
            self.generation_log["stats"]["template"] += 1
        else:
            script = self._call_llm(output)
            if script:
                log_entry["method"] = "llm"
                self.generation_log["stats"]["llm"] += 1
            else:
                log_entry["status"] = "skipped"
                self.generation_log["stats"]["skipped"] += 1
                script = self._placeholder_script(output)

        self.generation_log["outputs"].append(log_entry)
        return script

    def _try_template(self, output: Dict) -> Optional[str]:
        output_id = output["output_id"]
        title = output.get("title", "")

        search_text = f"{output_id} {title}".lower()

        for template_name, template_info in self.TEMPLATES.items():
            if re.search(template_info["pattern"], search_text, re.IGNORECASE):
                return self._render_template(template_name, output)

        return None

    def _render_template(self, template_name: str, output: Dict) -> Optional[str]:
        output_id = output["output_id"]
        schema = output.get("schema", "baseline")
        title = output.get("title", "")
        population = output.get("population", "SAFFL")
        variables = output.get("variables", [])

        if template_name == "demographics":
            return self._demographics_template(
                output_id, schema, title, population, variables
            )
        elif template_name == "ae_summary":
            return self._ae_summary_template(
                output_id, schema, title, population, variables
            )
        elif template_name == "listing":
            return self._listing_template(
                output_id, schema, title, population, variables
            )

        return None

    def _demographics_template(
        self,
        output_id: str,
        schema: str,
        title: str,
        population: str,
        variables: List[str],
    ) -> str:
        return f'''"""
{title}
Output ID: {output_id}
Schema: {schema}
Population: {population}
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

import pandas as pd
import numpy as np
from prism import Database
from olympus.gold.stats import desc_stats_continuous, desc_stats_categorical, format_stat

def main():
    db = Database("study.duckdb")
    
    print(f"Computing: {output_id} - {title}")
    
    df = db.query_df("""
        SELECT usubjid, trta, {population.lower()}, age, sex, race
        FROM silver.{schema}
        WHERE {population.lower()} = 'Y'
    """)
    
    print(f"  Subjects: {{len(df)}}")
    
    results = []
    
    for trta in df['trta'].unique():
        subset = df[df['trta'] == trta]
        
        if 'age' in df.columns:
            stats = desc_stats_continuous(subset['age'].dropna().tolist())
            for stat_name, stat_value in stats.items():
                if stat_value is not None:
                    results.append({{
                        'output_id': '{output_id}',
                        'group1_name': 'TRTA',
                        'group1_value': trta,
                        'variable': 'AGE',
                        'stat_name': stat_name,
                        'stat_value': stat_value,
                        'stat_display': format_stat(stat_name, stat_value)
                    }})
        
        for var in ['sex', 'race']:
            if var in df.columns:
                cat_stats = desc_stats_categorical(subset[var].dropna().tolist())
                for cs in cat_stats:
                    results.append({{
                        'output_id': '{output_id}',
                        'group1_name': 'TRTA',
                        'group1_value': trta,
                        'variable': var.upper(),
                        'category': cs['category'],
                        'stat_name': 'n',
                        'stat_value': cs['n'],
                        'stat_display': str(cs['n'])
                    }})
                    results.append({{
                        'output_id': '{output_id}',
                        'group1_name': 'TRTA',
                        'group1_value': trta,
                        'variable': var.upper(),
                        'category': cs['category'],
                        'stat_name': 'pct',
                        'stat_value': cs['pct'],
                        'stat_display': f"{{cs['pct']:.1f}}%"
                    }})
    
    db.execute("DELETE FROM gold.{schema} WHERE output_id = ?", ('{output_id}',))
    
    for row in results:
        db.execute("""
            INSERT INTO gold.{schema}
            (output_id, group1_name, group1_value, variable, category, stat_name, stat_value, stat_display)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row['output_id'], row['group1_name'], row['group1_value'],
            row['variable'], row.get('category'), row['stat_name'],
            row['stat_value'], row['stat_display']
        ))
    
    print(f"  Results inserted: {{len(results)}} rows")
    
    db.close()
    print("Done!")

if __name__ == '__main__':
    main()
'''

    def _ae_summary_template(
        self,
        output_id: str,
        schema: str,
        title: str,
        population: str,
        variables: List[str],
    ) -> str:
        return f'''"""
{title}
Output ID: {output_id}
Schema: {schema}
Population: {population}
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

import pandas as pd
from prism import Database

def main():
    db = Database("study.duckdb")
    
    print(f"Computing: {output_id} - {title}")
    
    df = db.query_df("""
        SELECT usubjid, trta, teaefl, aesoc, aedecod
        FROM silver.{schema}
        WHERE teaefl = 'Y'
    """)
    
    print(f"  TEAE records: {{len(df)}}")
    
    results = []
    
    for trta in df['trta'].unique():
        subset = df[df['trta'] == trta]
        n_subj = subset['usubjid'].nunique()
        n_events = len(subset)
        
        results.append({{
            'output_id': '{output_id}',
            'group1_name': 'TRTA',
            'group1_value': trta,
            'variable': 'ANY_TEAE',
            'stat_name': 'n_subj',
            'stat_value': n_subj,
            'stat_display': str(n_subj)
        }})
        
        results.append({{
            'output_id': '{output_id}',
            'group1_name': 'TRTA',
            'group1_value': trta,
            'variable': 'ANY_TEAE',
            'stat_name': 'n_events',
            'stat_value': n_events,
            'stat_display': str(n_events)
        }})
    
    db.execute("DELETE FROM gold.{schema} WHERE output_id = ?", ('{output_id}',))
    
    for row in results:
        db.execute("""
            INSERT INTO gold.{schema}
            (output_id, group1_name, group1_value, variable, stat_name, stat_value, stat_display)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            row['output_id'], row['group1_name'], row['group1_value'],
            row['variable'], row['stat_name'], row['stat_value'], row['stat_display']
        ))
    
    print(f"  Results inserted: {{len(results)}} rows")
    
    db.close()
    print("Done!")

if __name__ == '__main__':
    main()
'''

    def _listing_template(
        self,
        output_id: str,
        schema: str,
        title: str,
        population: str,
        variables: List[str],
    ) -> str:
        var_list = ", ".join([v.lower() for v in variables]) if variables else "*"

        return f'''"""
{title}
Output ID: {output_id}
Schema: {schema}
Population: {population}
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

import pandas as pd
from prism import Database

def main():
    db = Database("study.duckdb")
    
    print(f"Generating listing: {output_id} - {title}")
    
    df = db.query_df("""
        SELECT {var_list}
        FROM silver.{schema}
        WHERE 1=1
    """)
    
    print(f"  Records: {{len(df)}}")
    
    output_csv = f"generated/{{output_id}}.csv"
    df.to_csv(output_csv, index=False)
    print(f"  Exported: {{output_csv}}")
    
    db.close()
    print("Done!")

if __name__ == '__main__':
    main()
'''

    def _call_llm(self, output: Dict) -> Optional[str]:
        if not self.api_key:
            logger.warning(
                f"No DEEPSEEK_API_KEY, skipping LLM for {output['output_id']}"
            )
            return None

        prompt = self._build_prompt(output)
        content = _deprecated_call_deepseek(prompt)

        if content:
            return self._extract_code(content, output)
        return None

    def _build_prompt(self, output: Dict) -> str:
        output_id = output["output_id"]
        output_type = output.get("output_type", "table")
        schema = output.get("schema", "baseline")
        title = output.get("title", "")
        population = output.get("population", "SAFFL")
        variables = output.get("variables", [])

        return f"""你是一个临床试验数据统计的Python专家。

## 任务
生成一个Python脚本来计算统计表。

## 输出定义
- Output ID: {output_id}
- Type: {output_type}
- Schema: {schema}
- Title: {title}
- Population: {population}
- Variables: {", ".join(variables) if variables else "未指定"}

## 数据库
- DuckDB 数据库文件: study.duckdb
- 源数据表: silver.{schema}
- 目标表: gold.{schema}

## Gold表结构
- output_id: 输出ID
- group1_name: 分组变量名 (如 'TRTA')
- group1_value: 分组值 (如 'Drug A', 'Placebo')
- variable: 变量名
- category: 分类值 (可空)
- stat_name: 统计量名 ('n', 'mean', 'sd', 'median', 'pct')
- stat_value: 统计值
- stat_display: 格式化显示值

## 要求
1. 使用 prism.Database 连接数据库
2. 从 silver.{schema} 读取数据
3. 按 trta 分组计算统计
4. 清空旧数据后插入新数据
5. 只输出Python代码，用```python包裹

## 模板
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from prism import Database

def main():
    db = Database("study.duckdb")
    # TODO: 实现统计计算
    db.close()

if __name__ == '__main__':
    main()
```

## Python代码
"""

    def _extract_code(self, content: str, output: Dict) -> str:
        code = _deprecated_extract_code_block(content, "python")

        header = f'''"""
{output.get("title", output["output_id"])}
Output ID: {output["output_id"]}
Generated by LLM: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
'''
        return header + code

    def _placeholder_script(self, output: Dict) -> str:
        output_id = output["output_id"]
        schema = output.get("schema", "baseline")
        title = output.get("title", "")

        return f'''"""
{title}
Output ID: {output_id}
Schema: {schema}
Status: SKIPPED - Manual implementation required
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from prism import Database

def main():
    db = Database("study.duckdb")
    
    # TODO: Implement this analysis manually
    # 1. Read data from silver.{schema}
    # 2. Compute statistics
    # 3. Write to gold.{schema}
    
    print("This script needs manual implementation")
    
    db.close()

if __name__ == '__main__':
    main()
'''
