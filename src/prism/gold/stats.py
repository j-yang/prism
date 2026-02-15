import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional


def desc_stats_continuous(values: List[float]) -> Dict[str, Any]:
    arr = np.array([v for v in values if v is not None and not pd.isna(v)])

    if len(arr) == 0:
        return {
            "n": 0,
            "mean": None,
            "sd": None,
            "median": None,
            "min": None,
            "max": None,
        }

    return {
        "n": len(arr),
        "mean": round(float(np.mean(arr)), 2),
        "sd": round(float(np.std(arr, ddof=1)), 2),
        "median": round(float(np.median(arr)), 2),
        "min": round(float(np.min(arr)), 2),
        "max": round(float(np.max(arr)), 2),
    }


def desc_stats_categorical(values: List[str]) -> List[Dict[str, Any]]:
    series = pd.Series([v for v in values if v is not None and not pd.isna(v)])

    if len(series) == 0:
        return []

    total = len(series)
    counts = series.value_counts()

    results = []
    for category, n in counts.items():
        results.append(
            {"category": str(category), "n": int(n), "pct": round(100.0 * n / total, 1)}
        )

    return results


def format_stat(stat_name: str, stat_value: Any, decimal: int = 1) -> str:
    if stat_value is None:
        return ""

    if stat_name == "n":
        return str(int(stat_value))
    elif stat_name == "pct":
        return f"{stat_value:.{decimal}f}%"
    elif stat_name in ("mean", "sd", "median", "min", "max"):
        return f"{stat_value:.{decimal}f}"
    else:
        return str(stat_value)


def compute_table_stats(
    df: pd.DataFrame,
    variables: List[Dict],
    group_col: str = "trta",
    filter_condition: str = None,
) -> List[Dict]:
    if filter_condition:
        df = df.query(filter_condition)

    results = []
    row_order = 0

    for var in variables:
        var_name = var["name"]
        var_type = var.get("type", "continuous")

        if var_name not in df.columns:
            continue

        for group_value in df[group_col].unique():
            subset = df[df[group_col] == group_value]

            if var_type == "continuous":
                stats = desc_stats_continuous(subset[var_name].tolist())

                for stat_name, stat_value in stats.items():
                    if stat_value is not None:
                        results.append(
                            {
                                "group1_name": group_col.upper(),
                                "group1_value": group_value,
                                "variable": var_name.upper(),
                                "category": None,
                                "stat_name": stat_name,
                                "stat_value": stat_value,
                                "stat_display": format_stat(stat_name, stat_value),
                                "row_order": row_order,
                            }
                        )
                        row_order += 1

            elif var_type == "categorical":
                stats = desc_stats_categorical(subset[var_name].tolist())

                for cat_stat in stats:
                    results.append(
                        {
                            "group1_name": group_col.upper(),
                            "group1_value": group_value,
                            "variable": var_name.upper(),
                            "category": cat_stat["category"],
                            "stat_name": "n",
                            "stat_value": cat_stat["n"],
                            "stat_display": str(cat_stat["n"]),
                            "row_order": row_order,
                        }
                    )
                    row_order += 1

                    results.append(
                        {
                            "group1_name": group_col.upper(),
                            "group1_value": group_value,
                            "variable": var_name.upper(),
                            "category": cat_stat["category"],
                            "stat_name": "pct",
                            "stat_value": cat_stat["pct"],
                            "stat_display": format_stat("pct", cat_stat["pct"]),
                            "row_order": row_order,
                        }
                    )
                    row_order += 1

    return results
