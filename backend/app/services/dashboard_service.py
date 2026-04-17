from __future__ import annotations

from datetime import datetime
from io import StringIO
import math
import re
from typing import Iterable
from urllib.parse import quote_plus

import pandas as pd

from app.services.data_store import (
    get_active_dataset,
    get_active_report,
    list_uploaded_months,
    load_dashboard_dataset,
)


TITLE_TO_YEAR_KEY = {
    "1st YEAR VP YIELD": "First_Year",
    "2nd YEAR VP YIELD": "Second_Year",
    "3rd YEAR VP YIELD": "Third_Year",
    "4th YEAR VP YIELD": "Fourth_Year",
    "5th YEAR VP YIELD": "Fifth_Year",
    "VP YIELD": "VP",
    "SD YIELD": "SD",
    "TOTAL (VP + SD) YIELD": "VP & SD",
}

YEAR_KEY_TO_LABEL = {v: k for k, v in TITLE_TO_YEAR_KEY.items()}

YEAR_DISPLAY_ORDER = [
    "First_Year",
    "Second_Year",
    "Third_Year",
    "Fourth_Year",
    "Fifth_Year",
    "VP",
    "SD",
    "VP & SD",
]

PLANTATION_BY_REGION = {
    "TK": "TTEL",
    "NO": "TTEL",
    "TTEL_LC": "TTEL",
    "HT": "KVPL",
    "NE": "KVPL",
    "KVPL_LC": "KVPL",
    "UC": "HPL",
    "LD": "HPL",
    "HPL_LC": "HPL",
}

REGION_DISPLAY_NAMES = {
    "TK": "Talawakelle",
    "NO": "Nanu Oya",
    "TTEL_LC": "TTEL_LC",
    "NE": "Nuwara Eliya",
    "HT": "Hatton",
    "KVPL_LC": "KVPL_LC",
    "UC": "UPCOT",
    "LD": "Lindula",
    "HPL_LC": "HPL_LC",
}

PLANTATION_DISPLAY_NAMES = {
    "TTEL": "Talawakelle",
    "KVPL": "Kelani Valley",
    "HPL": "Horana",
    "HAYLEYS": "Hayleys Plantations",
}


def display_region_label(region: str, plantation: str = "") -> str:
    code = str(region or "").strip()
    if not code:
        return ""
    if code in REGION_DISPLAY_NAMES:
        return REGION_DISPLAY_NAMES[code]
    return code.replace("_", " - ")


def display_plantation_label(plantation: str) -> str:
    code = str(plantation or "").strip()
    if not code:
        return ""
    return PLANTATION_DISPLAY_NAMES.get(code, code)

METRIC_LABELS = {
    "Division_Yield": "Division Yield",
    "Estate_Yield": "Estate Yield",
    "Regional_Yield": "Regional Yield",
    "Benchmark": "Benchmark",
    "80%_OF_BENCHMARK": "80% of Benchmark",
    "70%_OF_BENCHMARK": "70% of Benchmark",
    "50%_OF_BENCHMARK": "50% of Benchmark",
    "Bush_Count": "Bush Count",
    "Estate_Extent": "Estate Extent",
    "Division_Extent": "Division Extent",
    "Hectare": "Hectare",
    "Stand_per_Ha": "Stand per Ha",
    "Average_Rounds": "Average Rounds",
    "Green_Leaf": "Green Leaf",
}

METRIC_COLUMN_MAP = {
    "Division_Yield": "divisional_yield",
    "Estate_Yield": "estate_yield",
    "Regional_Yield": "regional_average",
    "Benchmark": "benchmark",
    "80%_OF_BENCHMARK": "benchmark_80",
    "70%_OF_BENCHMARK": "benchmark_70",
    "50%_OF_BENCHMARK": "benchmark_50",
    "Bush_Count": "bush_count",
    "Estate_Extent": "estate_extend",
    "Division_Extent": "divisional_extend",
    "Hectare": "hectare",
    "Stand_per_Ha": "stand_per_ha",
    "Average_Rounds": "average_rounds",
    "Green_Leaf": "green_leaf",
}

ESTATE_LEVEL_METRICS = {
    "Estate_Yield",
    "Regional_Yield",
    "Benchmark",
    "80%_OF_BENCHMARK",
    "70%_OF_BENCHMARK",
    "50%_OF_BENCHMARK",
    "Estate_Extent",
}

AGGREGATORS = {
    "divisional_yield": "mean",
    "estate_yield": "first",
    "regional_average": "first",
    "benchmark": "first",
    "benchmark_80": "first",
    "benchmark_70": "first",
    "benchmark_50": "first",
    "bush_count": "sum",
    "estate_extend": "first",
    "divisional_extend": "sum",
    "hectare": "sum",
    "stand_per_ha": "mean",
    "average_rounds": "mean",
    "green_leaf": "sum",
}


def _month_label(selected_month: str) -> str:
    try:
        return datetime.strptime(selected_month, "%Y-%m").strftime("%b %Y")
    except Exception:
        return selected_month


def plantation_for_region(region: str) -> str:
    return PLANTATION_BY_REGION.get(str(region).strip().upper(), "Unknown")


def build_google_map_link(plantation: str, estate: str, division: str, code: str = "") -> str:
    parts = [division, estate, plantation, code, "Sri Lanka"]
    return f"https://www.google.com/maps/search/?api=1&query={quote_plus(' '.join([p for p in parts if p]).strip())}"


def build_dashboard_dataset(calc_result, selected_month: str) -> pd.DataFrame:
    rows: list[dict] = []
    month_label = _month_label(selected_month)

    for region, sheets in calc_result.outputs.items():
        plantation = plantation_for_region(region)
        for title, sheet_df in sheets.items():
            if title == "ABSTRACT SUMMARY":
                continue

            year_key = TITLE_TO_YEAR_KEY.get(title, title)
            clean_sheet = sheet_df.where(pd.notnull(sheet_df), 0)
            for _, row in clean_sheet.iterrows():
                estate = str(row.get("estate", "")).strip()
                division = str(row.get("division", "")).strip()
                code = str(row.get("code", "")).strip()
                rows.append(
                    {
                        "selected_month": selected_month,
                        "month_label": month_label,
                        "plantation": plantation,
                        "region": region,
        "region_label": display_region_label(region),
                        "year": year_key,
                        "year_label": title,
                        "estate": estate,
                        "division": division,
                        "division_key": f"{plantation}|{region}|{estate}|{division}|{code}",
                        "code": code,
                        "divisional_yield": float(row.get("yph", 0) or 0),
                        "estate_yield": float(row.get("estate_avg", 0) or 0),
                        "regional_average": float(row.get("regional_avg", 0) or 0),
                        "benchmark": float(row.get("benchmark", 0) or 0),
                        "benchmark_80": float(row.get("bm_80", 0) or 0),
                        "benchmark_70": float(row.get("bm_70", 0) or 0),
                        "benchmark_50": float(row.get("bm_50", 0) or 0),
                        "bush_count": float(row.get("bc", 0) or 0),
                        "estate_extend": float(row.get("estate_total_ha", 0) or 0),
                        "divisional_extend": float(row.get("div_ext", 0) or 0),
                        "hectare": float(row.get("ha", 0) or 0),
                        "stand_per_ha": float(row.get("stand_per_ha", 0) or 0),
                        "average_rounds": float(row.get("todate_rounds", 0) or 0),
                        "monthly_rounds": float(row.get("rounds_month", 0) or 0),
                        "green_leaf": float(row.get("green_leaf", 0) or 0),
                        "division_pct": float(row.get("pct", 0) or 0),
                    }
                )
    return pd.DataFrame(rows)


def get_active_dataset_df() -> tuple[str | None, pd.DataFrame | None]:
    selected_month = get_active_dataset()
    if not selected_month:
        return None, None
    df = load_dashboard_dataset(selected_month)
    if df is None or df.empty:
        return selected_month, None
    return selected_month, df.fillna("")


def _sorted_unique(series: Iterable[str]) -> list[str]:
    values = sorted({str(v).strip() for v in series if str(v).strip()}, key=lambda x: x.lower())
    return values


def get_dashboard_status(df_override=None, selected_month_override: str | None = None) -> dict:
    selected_month = selected_month_override
    df = df_override
    if selected_month is None and df is None:
        selected_month, df = get_active_dataset_df()

    active_report = get_active_report()
    if df is None or df.empty:
        return {
            "has_dataset": False,
            "selected_month": selected_month,
            "uploaded_months": list_uploaded_months(),
            "active_report": active_report,
        }

    return {
        "has_dataset": True,
        "selected_month": selected_month,
        "month_label": str(df["month_label"].iloc[0]),
        "row_count": int(len(df)),
        "regions": _sorted_unique(df["region"]),
        "plantations": _sorted_unique(df["plantation"]),
        "estates": _sorted_unique(df["estate"]),
        "divisions": _sorted_unique(df["division"]),
        "uploaded_months": list_uploaded_months(),
        "active_report": active_report,
    }


def get_filter_options(df: pd.DataFrame) -> dict:
    divisions = (
        df[["division_key", "plantation", "region", "estate", "division", "code"]]
        .drop_duplicates()
        .sort_values(["plantation", "estate", "division"])
    )

    return {
        "plantations": _sorted_unique(df["plantation"]),
        "regions": _sorted_unique(df["region"]),
        "estates": _sorted_unique(df["estate"]),
        "years": [value for value in YEAR_DISPLAY_ORDER if value in set(df["year"])],
        "metrics": [{"value": key, "label": label} for key, label in METRIC_LABELS.items() if key not in {"80%_OF_BENCHMARK", "70%_OF_BENCHMARK", "50%_OF_BENCHMARK"}],
        "benchmarks": [
            {"value": "80%_OF_BENCHMARK", "label": "80% of Benchmark"},
            {"value": "70%_OF_BENCHMARK", "label": "70% of Benchmark"},
            {"value": "50%_OF_BENCHMARK", "label": "50% of Benchmark"},
        ],
        "divisions": divisions.to_dict(orient="records"),
    }


def _apply_filters(
    df: pd.DataFrame,
    plantation: str = "",
    region: str = "",
    estate: str = "",
    division: str = "",
    year: str = "",
) -> pd.DataFrame:
    out = df.copy()
    if plantation:
        out = out[out["plantation"].astype(str).str.lower() == plantation.lower()]
    if region:
        out = out[out["region"].astype(str).str.lower() == region.lower()]
    if estate:
        out = out[out["estate"].astype(str).str.lower() == estate.lower()]
    if division:
        out = out[out["division"].astype(str).str.lower() == division.lower()]
    if year:
        out = out[out["year"].astype(str).str.lower() == year.lower()]
    return out.reset_index(drop=True)


def _first_or_none(df: pd.DataFrame) -> dict | None:
    if df.empty:
        return None
    return df.iloc[0].to_dict()


def _entity_dedupe_key(row: pd.Series, metric_key: str) -> str:
    if metric_key in ESTATE_LEVEL_METRICS:
        return f"{row.get('plantation')}|{row.get('region')}|{row.get('estate')}|{row.get('year')}"
    return f"{row.get('plantation')}|{row.get('region')}|{row.get('estate')}|{row.get('division')}|{row.get('year')}|{row.get('code')}"


def _value_for_row(row: pd.Series, metric_key: str):
    column = METRIC_COLUMN_MAP.get(metric_key, "divisional_yield")
    return row.get(column, 0)


def _serialize_row(row: pd.Series, metric_key: str) -> dict:
    value = _value_for_row(row, metric_key)
    division_value = "" if metric_key in ESTATE_LEVEL_METRICS else row.get("division", "")
    return {
        "plantation": row.get("plantation", ""),
        "plantation_label": display_plantation_label(str(row.get("plantation", ""))),
        "region": row.get("region", ""),
        "region_label": display_region_label(str(row.get("region", "")), str(row.get("plantation", ""))),
        "estate": row.get("estate", ""),
        "division": division_value,
        "division_key": row.get("division_key", ""),
        "code": row.get("code", ""),
        "year": row.get("year", ""),
        "year_label": row.get("year_label", ""),
        "value": float(value) if value not in ("", None) else 0,
        "metric": metric_key,
        "metric_label": METRIC_LABELS.get(metric_key, metric_key),
        "average_rounds": float(row.get("average_rounds", 0) or 0),
        "bush_count": float(row.get("bush_count", 0) or 0),
        "regional_average": float(row.get("regional_average", 0) or 0),
        "benchmark": float(row.get("benchmark", 0) or 0),
        "map_url": build_google_map_link(
            str(row.get("plantation", "")),
            str(row.get("estate", "")),
            str(row.get("division", "")),
            str(row.get("code", "")),
        ),
    }


def _overview_rows(df: pd.DataFrame) -> list[dict]:
    deduped = (
        df.sort_values(["plantation", "estate", "division", "year"])
        [["plantation", "region", "estate", "division", "division_key", "code", "average_rounds"]]
        .drop_duplicates(subset=["plantation", "region", "estate", "division", "code"])
    )
    rows = []
    for _, row in deduped.iterrows():
        item = row.to_dict()
        item["map_url"] = build_google_map_link(
            str(row.get("plantation", "")),
            str(row.get("estate", "")),
            str(row.get("division", "")),
            str(row.get("code", "")),
        )
        rows.append(item)
    return rows


def _dedupe_rows(df: pd.DataFrame, metric_key: str) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for _, row in df.iterrows():
        key = _entity_dedupe_key(row, metric_key)
        if key in seen:
            continue
        seen.add(key)
        out.append(_serialize_row(row, metric_key))
    return out


def _compare(value: float, operator: str, threshold: float) -> bool:
    if operator == ">":
        return value > threshold
    if operator == ">=":
        return value >= threshold
    if operator == "<":
        return value < threshold
    if operator == "<=":
        return value <= threshold
    if operator in {"=", "=="}:
        return value == threshold
    if operator == "!=":
        return value != threshold
    return False


def get_region_summary(df: pd.DataFrame, region: str, year: str) -> dict | None:
    region_df = _apply_filters(df, region=region, year=year)
    row = _first_or_none(region_df)
    if not row:
        return None
    return {
        "region": region,
        "region_label": display_region_label(region),
        "year": year,
        "regional_average": float(row.get("regional_average", 0) or 0),
        "benchmark": float(row.get("benchmark", 0) or 0),
    }


def get_estate_summary(
    df: pd.DataFrame,
    plantation: str,
    estate: str,
    year: str,
    division: str = "",
) -> dict | None:
    estate_df = _apply_filters(df, plantation=plantation, estate=estate, year=year, division=division)
    row = _first_or_none(estate_df)
    if not row:
        return None

    out = {
        "plantation": row.get("plantation", ""),
        "plantation_label": display_plantation_label(str(row.get("plantation", ""))),
        "region": row.get("region", ""),
        "region_label": display_region_label(str(row.get("region", "")), str(row.get("plantation", ""))),
        "estate": row.get("estate", ""),
        "year": row.get("year", ""),
        "estate_extent": float(row.get("estate_extend", 0) or 0),
        "estate_yield": float(row.get("estate_yield", 0) or 0),
        "regional_average": float(row.get("regional_average", 0) or 0),
        "benchmark": float(row.get("benchmark", 0) or 0),
    }

    benchmark = float(row.get("benchmark", 0) or 0)
    estate_yield = float(row.get("estate_yield", 0) or 0)
    out["estate_percentage"] = round((estate_yield / benchmark) * 100, 2) if benchmark else 0.0

    if division:
        div_yield = float(row.get("divisional_yield", 0) or 0)
        out["divisional_yield"] = div_yield
        out["divisional_extend"] = float(row.get("divisional_extend", 0) or 0)
        out["divisional_percentage"] = round((div_yield / benchmark) * 100, 2) if benchmark else 0.0

    return out


def run_dashboard_query(
    df: pd.DataFrame,
    plantation: str = "",
    region: str = "",
    estate: str = "",
    division: str = "",
    year: str = "",
    metric: str = "Division_Yield",
    operator: str = "",
    value: float | None = None,
    rank_dir: str = "",
    count: int = 10,
    benchmark_metric: str = "",
) -> dict:
    metric_key = benchmark_metric or metric or "Division_Yield"
    filtered = _apply_filters(df, plantation=plantation, region=region, estate=estate, division=division, year=year)

    if filtered.empty:
        return {
            "mode": "EMPTY",
            "answer": "No matching records were found for the current selection.",
            "rows": [],
            "metric": metric_key,
        }

    if rank_dir:
        ranked = filtered.copy()
        if metric_key in ESTATE_LEVEL_METRICS:
            ranked = ranked.drop_duplicates(subset=["plantation", "region", "estate", "year"])
        else:
            ranked = ranked.drop_duplicates(subset=["plantation", "region", "estate", "division", "year", "code"])
        metric_column = METRIC_COLUMN_MAP[metric_key]
        ranked = ranked.sort_values(metric_column, ascending=rank_dir.lower() == "bottom")
        ranked = ranked.head(max(count, 1))
        rows = _dedupe_rows(ranked, metric_key)
        return {
            "mode": "RANK",
            "answer": f"{rank_dir.title()} {len(rows)} rows by {METRIC_LABELS.get(metric_key, metric_key)}.",
            "rows": rows,
            "metric": metric_key,
        }

    if value is not None and operator:
        metric_column = METRIC_COLUMN_MAP[metric_key]
        compared = filtered.copy()
        compared = compared[compared[metric_column].apply(lambda item: _compare(float(item or 0), operator, float(value)))]
        rows = _dedupe_rows(compared, metric_key)
        return {
            "mode": "FILTER",
            "answer": f"{len(rows)} rows where {METRIC_LABELS.get(metric_key, metric_key)} {operator} {value}.",
            "rows": rows,
            "metric": metric_key,
        }

    if any([estate, division, year, benchmark_metric]):
        rows = _dedupe_rows(filtered, metric_key)
        title = METRIC_LABELS.get(metric_key, metric_key)
        subject = estate or division or display_region_label(region, plantation) or display_plantation_label(plantation) or "selection"
        return {
            "mode": "EXACT",
            "answer": f"{title} results for {subject}.",
            "rows": rows,
            "metric": metric_key,
        }

    rows = _overview_rows(filtered)
    return {
        "mode": "OVERVIEW",
        "answer": f"{len(rows)} locations are available in the active dataset.",
        "rows": rows,
        "metric": metric_key,
    }


def export_rows_csv(rows: list[dict]) -> str:
    if not rows:
        return ""
    frame = pd.DataFrame(rows)
    buffer = StringIO()
    frame.to_csv(buffer, index=False)
    return buffer.getvalue()


def get_chart_data(
    df: pd.DataFrame,
    region: str,
    year: str,
    metric: str,
    focus_estate: str = "",
    focus_division: str = "",
) -> dict:
    base = _apply_filters(df, region=region, year=year)
    if base.empty:
        return {"title": "No chart data", "bars": [], "unit": "YPH"}

    metric_column = METRIC_COLUMN_MAP.get(metric, "divisional_yield")
    metric_label = METRIC_LABELS.get(metric, metric)

    if focus_estate:
        chart_df = (
            base.groupby(["estate"], dropna=False)
            .agg(
                {
                    metric_column: AGGREGATORS.get(metric_column, "mean"),
                    "benchmark": "mean",
                    "regional_average": "mean",
                }
            )
            .reset_index()
            .sort_values(metric_column, ascending=False)
        )
        label_key = "estate"
        title = f"{metric_label} across estates in {region} ({year})"
        focus_label = focus_estate
    else:
        division_base = base
        if focus_division:
            division_base = division_base[
                division_base["division"].astype(str).str.lower() == focus_division.lower()
            ]
        chart_df = (
            division_base.groupby(["division"], dropna=False)
            .agg(
                {
                    metric_column: AGGREGATORS.get(metric_column, "mean"),
                    "benchmark": "mean",
                    "regional_average": "mean",
                }
            )
            .reset_index()
            .sort_values(metric_column, ascending=False)
            .head(12)
        )
        label_key = "division"
        title = f"{metric_label} inside {region} ({year})"
        focus_label = focus_division

    bars = []
    for _, row in chart_df.iterrows():
        label = str(row.get(label_key, "")).strip()
        bars.append(
            {
                "label": label,
                "value": round(float(row.get(metric_column, 0) or 0), 2),
                "highlight": label.lower() == focus_label.lower() if focus_label else False,
            }
        )

    reference = {}
    if not chart_df.empty:
        reference = {
            "benchmark": round(float(chart_df["benchmark"].mean()), 2),
            "regional_average": round(float(chart_df["regional_average"].mean()), 2),
        }

    return {
        "title": title,
        "metric": metric,
        "metric_label": metric_label,
        "bars": bars,
        "reference": reference,
        "focus_label": focus_label,
    }



def _normalize_match_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def _contains_phrase(haystack: str, needle: str, allow_substring: bool = False) -> bool:
    clean_haystack = f" {_normalize_match_text(haystack)} "
    clean_needle = _normalize_match_text(needle)
    if not clean_needle:
        return False
    if allow_substring:
        return clean_needle in clean_haystack
    return f" {clean_needle} " in clean_haystack


def parse_dashboard_question(df: pd.DataFrame, question: str) -> dict:
    text = (question or "").strip()
    lowered = text.lower()

    inferred = {
        "plantation": "",
        "region": "",
        "estate": "",
        "division": "",
        "year": "",
        "metric": "Estate_Yield" if "estate" in lowered else "Division_Yield",
        "operator": "",
        "value": None,
        "rank_dir": "",
        "count": 10,
        "benchmark_metric": "",
    }

    estates = sorted(_sorted_unique(df["estate"]), key=len, reverse=True)
    regions = sorted(_sorted_unique(df["region"]), key=len, reverse=True)
    plantations = sorted(_sorted_unique(df["plantation"]), key=len, reverse=True)
    divisions = sorted(_sorted_unique(df["division"]), key=len, reverse=True)

    for value in estates:
        if _contains_phrase(text, value, allow_substring=False):
            inferred["estate"] = value
            break

    for value in plantations:
        if _contains_phrase(text, value, allow_substring=False):
            inferred["plantation"] = value
            break

    for value in regions:
        if len(value) <= 3:
            if re.search(rf"\b{re.escape(value.lower())}\b", lowered):
                inferred["region"] = value
                break
        elif _contains_phrase(text, value, allow_substring=False):
            inferred["region"] = value
            break

    for value in divisions:
        if inferred["estate"] and value.lower() == inferred["estate"].lower():
            continue
        if _contains_phrase(text, value, allow_substring=False):
            inferred["division"] = value
            break

    year_phrases = {
        "first year": "First_Year",
        "1st year": "First_Year",
        "second year": "Second_Year",
        "2nd year": "Second_Year",
        "third year": "Third_Year",
        "3rd year": "Third_Year",
        "fourth year": "Fourth_Year",
        "4th year": "Fourth_Year",
        "fifth year": "Fifth_Year",
        "5th year": "Fifth_Year",
        "vp & sd": "VP & SD",
        "vp and sd": "VP & SD",
        "total": "VP & SD",
        "vp yield": "VP",
        "sd yield": "SD",
    }
    for phrase, value in year_phrases.items():
        if phrase in lowered:
            inferred["year"] = value
            break

    metric_keywords = [
        ("division yield", "Division_Yield"),
        ("estate yield", "Estate_Yield"),
        ("regional yield", "Regional_Yield"),
        ("benchmark", "Benchmark"),
        ("bush count", "Bush_Count"),
        ("estate extent", "Estate_Extent"),
        ("division extent", "Division_Extent"),
        ("hectare", "Hectare"),
        ("stand per ha", "Stand_per_Ha"),
        ("average rounds", "Average_Rounds"),
        ("green leaf", "Green_Leaf"),
    ]
    for keyword, metric_key in metric_keywords:
        if keyword in lowered:
            inferred["metric"] = metric_key
            break

    if "80%" in lowered:
        inferred["benchmark_metric"] = "80%_OF_BENCHMARK"
    elif "70%" in lowered:
        inferred["benchmark_metric"] = "70%_OF_BENCHMARK"
    elif "50%" in lowered:
        inferred["benchmark_metric"] = "50%_OF_BENCHMARK"

    rank_match = re.search(r"\b(top|bottom|best|worst|highest|lowest)\s+(\d+)", lowered)
    if rank_match:
        inferred["rank_dir"] = "top" if rank_match.group(1) in {"top", "best", "highest"} else "bottom"
        inferred["count"] = int(rank_match.group(2))

    compare_patterns = [
        (r"(?:above|over|greater than)\s+(\d+(?:\.\d+)?)", ">"),
        (r"(?:below|under|less than)\s+(\d+(?:\.\d+)?)", "<"),
        (r"(?:at least|minimum)\s+(\d+(?:\.\d+)?)", ">="),
        (r"(?:at most|maximum)\s+(\d+(?:\.\d+)?)", "<="),
    ]
    for pattern, operator in compare_patterns:
        match = re.search(pattern, lowered)
        if match:
            inferred["operator"] = operator
            inferred["value"] = float(match.group(1))
            break

    if inferred["estate"] and not inferred["plantation"]:
        estate_rows = df[df["estate"].astype(str).str.lower() == inferred["estate"].lower()]
        if not estate_rows.empty:
            inferred["plantation"] = str(estate_rows.iloc[0]["plantation"])
            inferred["region"] = str(estate_rows.iloc[0]["region"])

    return inferred

