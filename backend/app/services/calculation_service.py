from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import re
import math
import pandas as pd

GREEN_LEAF_FACTOR = 4.65
BENCHMARK_PERCENTAGES = [80, 70, 50]

REGION_ALIASES = {
    "LC": "TTEL_LC",
    "RB": "HT",
}

ESTATE_KEY_ALIASES = {
    "GREATWESTERN": "GREATWESTERN",
    "NUWARAELIYA": "NUWARAELIYA",
    "UDARADELLA": "UDARADELLA",
    "STOCKHHOLM": "STOCKHOLM",
    "BAMBRAKELLY": "BAMBARAKELLY",
}

DIVISION_KEY_ALIASES = {
    "BLAIRAVON": "BLARIVON",
    "BLAIRVON": "BLARIVON",
    "RAHANWATTE": "RAHANWATTA",
    "QUEENWOOD": "QUEENWOOD",
    "MOUSAELLALOWERDIV": "MOUSAELLALOWER",
    "MOUSAELLAUPPERDIV": "MOUSAELLAUPPER",
    "KITHULGALA": "KITULGALA",
    "STOCKHHOLM": "STOCKHOLM",
}

AGE_GROUPS = {
    "1st YEAR VP YIELD": (1, 12),
    "2nd YEAR VP YIELD": (13, 24),
    "3rd YEAR VP YIELD": (25, 36),
    "4th YEAR VP YIELD": (37, 48),
    "5th YEAR VP YIELD": (49, 9999),
}

GROUP_PARAMS = {
    "1st YEAR VP YIELD": (9, 18),
    "2nd YEAR VP YIELD": (11, 20),
    "3rd YEAR VP YIELD": (11, 20),
    "4th YEAR VP YIELD": (12, 19),
    "5th YEAR VP YIELD": (12, 18),
    "VP YIELD": (11, 20),
    "SD YIELD": (8, 17),
    "TOTAL (VP + SD) YIELD": None,
}

LC_GROUP_PARAMS = {
    "1st YEAR VP YIELD": 18,
    "2nd YEAR VP YIELD": 20,
    "3rd YEAR VP YIELD": 20,
    "4th YEAR VP YIELD": 19,
    "5th YEAR VP YIELD": 18,
    "VP YIELD": 20,
    "SD YIELD": 17,
    "TOTAL (VP + SD) YIELD": None,
}

DIV_EXT_CANDIDATES = ["div_ext_fixed", "Div_Ext", "DIV_EXT", "division_extent", "div_ext"]
EST_EXT_CANDIDATES = ["estate_ext_fixed", "Est_Ext", "EST_EXT", "estate_extent", "est_ext", "estate_total_ha"]


@dataclass
class CalculationResult:
    selected_month: str
    outputs: dict[str, Any]


def _canonical_region(region: str) -> str:
    value = "" if region is None else str(region).strip().upper()
    return REGION_ALIASES.get(value, value)


def _slug(v) -> str:
    text = "" if v is None else str(v).strip().upper()
    if text == "NAN":
        return ""
    return re.sub(r"[^A-Z0-9]+", "", text)


def _estate_key(v) -> str:
    return ESTATE_KEY_ALIASES.get(_slug(v), _slug(v))


def _division_key(v) -> str:
    return DIVISION_KEY_ALIASES.get(_slug(v), _slug(v))


def _is_lc_region(region: str) -> bool:
    region = _canonical_region(region)
    return region in {"TTEL_LC", "KVPL_LC", "HPL_LC"}


def _first_present_column(df: pd.DataFrame | None, candidates: list[str]) -> str | None:
    if df is None or df.empty:
        return None
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _safe_sum(df: pd.DataFrame, col: str) -> float:
    if col not in df.columns or df.empty:
        return 0.0
    return float(pd.to_numeric(df[col], errors="coerce").fillna(0).sum())


def _round_half_up(value: float, ndigits: int = 0) -> float:
    factor = 10 ** ndigits
    if value >= 0:
        return math.floor(value * factor + 0.5) / factor
    return math.ceil(value * factor - 0.5) / factor


def _safe_first_int(series: pd.Series) -> int:
    vals = pd.to_numeric(series, errors="coerce").dropna()
    if vals.empty:
        return 0
    return int(_round_half_up(float(vals.iloc[0])))


def _crop_sum(df: pd.DataFrame) -> float:
    return _safe_sum(df, "crop")


def _yph_from_crop_ha(crop: float, ha: float) -> int:
    return int(_round_half_up(crop / ha)) if ha > 0 else 0


def _regional_avg(df: pd.DataFrame) -> int:
    total_ha = _safe_sum(df, "hect")
    total_crop = _crop_sum(df)
    return _yph_from_crop_ha(total_crop, total_ha)


def _estate_avg_table(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["estate", "estate_avg"])

    grouped = (
        df.groupby("estate", dropna=False)
        .apply(
            lambda g: pd.Series(
                {
                    "ha": _safe_sum(g, "hect"),
                    "crop": _crop_sum(g),
                }
            )
        )
        .reset_index()
    )

    grouped["estate_avg"] = grouped.apply(
        lambda r: _yph_from_crop_ha(float(r["crop"]), float(r["ha"])),
        axis=1,
    )

    return grouped[["estate", "estate_avg"]]


def _division_extent_table(df_all: pd.DataFrame, master_df: pd.DataFrame | None = None) -> pd.DataFrame:
    col = _first_present_column(master_df, DIV_EXT_CANDIDATES)
    source = master_df if col else None

    if col is None:
        col = _first_present_column(df_all, DIV_EXT_CANDIDATES)
        source = df_all if col else None

    if source is not None and col is not None:
        out = source[["estate", "division", col]].copy()
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)
        out = (
            out.groupby(["estate", "division"], dropna=False)[col]
            .max()
            .reset_index()
            .rename(columns={col: "div_ext"})
        )
        return out

    return (
        df_all.groupby(["estate", "division"], dropna=False)["hect"]
        .sum()
        .reset_index()
        .rename(columns={"hect": "div_ext"})
    )


def _estate_total_ha_table(df_all: pd.DataFrame, master_df: pd.DataFrame | None = None) -> pd.DataFrame:
    col = _first_present_column(master_df, EST_EXT_CANDIDATES)
    source = master_df if col else None

    if col is None:
        col = _first_present_column(df_all, EST_EXT_CANDIDATES)
        source = df_all if col else None

    if source is not None and col is not None:
        out = source[["estate", col]].copy()
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)
        out = (
            out.groupby("estate", dropna=False)[col]
            .max()
            .reset_index()
            .rename(columns={col: "estate_total_ha"})
        )
        return out

    return (
        df_all.groupby("estate", dropna=False)["hect"]
        .sum()
        .reset_index()
        .rename(columns={"hect": "estate_total_ha"})
    )


def _all_divisions(df_all: pd.DataFrame, master_df: pd.DataFrame | None = None) -> pd.DataFrame:
    # Legacy outputs are driven by uploaded rows; do not surface master-only rows.
    source = df_all if df_all is not None and not df_all.empty else master_df

    cols = ["estate", "division", "code"]
    if source is None or source.empty:
        return pd.DataFrame(columns=cols)

    keep = [c for c in cols if c in source.columns]
    out = source[keep].drop_duplicates().copy()

    if "code" not in out.columns:
        out["code"] = out["division"].astype(str).str[:2].str.upper()

    return out.sort_values(["estate", "division"]).reset_index(drop=True)


def _prepare_source_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    for col in ["division", "field_no", "sd_vp", "code"]:
        if col in out.columns:
            out[col] = out[col].astype(str).str.strip()

    if "estate" in out.columns:
        out["estate"] = out["estate"].astype(str).str.strip().replace({
            "Great Western": "GreatWestern",
            "GREAT WESTERN": "GreatWestern",
            "Nuwara Eliya": "Nuwaraeliya",
            "UDA RADELLA": "Udaradella",
            "Uda Radella": "Udaradella",
            "STOCKHHOLM": "Stockholm",
            "BAMBRAKELLY": "Bambrakelly",
            "BAMBARAKELLY": "Bambrakelly",
        })

    if "age_months" in out.columns:
        out["age_months"] = pd.to_numeric(out["age_months"], errors="coerce").apply(lambda x: math.floor(x) if pd.notna(x) else x)

    for col in ["hect", "crop", "yph", "bc", "stand_per_ha", "lph"] + DIV_EXT_CANDIDATES + EST_EXT_CANDIDATES:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)

    pk_cols = [c for c in ["estate", "division", "field_no", "age_months", "sd_vp"] if c in out.columns]
    if pk_cols:
        out = out.drop_duplicates(subset=pk_cols, keep="first").reset_index(drop=True)

    return out


def _lc_lph(group_name: str, stand_per_ha: float) -> int:
    kg_per_round = LC_GROUP_PARAMS.get(group_name)
    if kg_per_round is None or stand_per_ha <= 0:
        return 0

    bushes_per_worker = 1000.0
    workers_per_ha = stand_per_ha / bushes_per_worker
    lph = workers_per_ha * kg_per_round
    return int(round(lph))


def _filter_to_master_pairs(df: pd.DataFrame, master_df: pd.DataFrame | None) -> pd.DataFrame:
    if master_df is None or master_df.empty:
        return df

    if "estate" not in df.columns or "division" not in df.columns:
        return df

    if "estate" not in master_df.columns or "division" not in master_df.columns:
        return df

    out = df.copy()
    out["_estate_key"] = out["estate"].map(_estate_key)
    out["_division_key"] = out["division"].map(_division_key)

    master_pairs = master_df.copy()
    master_pairs["_estate_key"] = master_pairs["estate"].map(_estate_key)
    master_pairs["_division_key"] = master_pairs["division"].map(_division_key)

    master_pairs = master_pairs[["_estate_key", "_division_key"]].drop_duplicates()

    out = out.merge(
        master_pairs,
        on=["_estate_key", "_division_key"],
        how="inner",
    )

    out = out.drop(columns=["_estate_key", "_division_key"])
    return out.reset_index(drop=True)


def process_group(
    filtered_df: pd.DataFrame,
    full_df: pd.DataFrame,
    group_name: str,
    use_estate_pct: bool,
    include_rounds: bool,
    months_in_period: int,
    region: str,
    master_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    region = _canonical_region(region)
    is_lc = _is_lc_region(region)

    filtered_df = _prepare_source_df(filtered_df)
    full_df = _prepare_source_df(full_df)
    master_df = _prepare_source_df(master_df) if master_df is not None and not master_df.empty else None

    full_divisions = _all_divisions(full_df, master_df=master_df)
    div_extent = _division_extent_table(full_df, master_df=master_df)
    estate_total_ha = _estate_total_ha_table(full_df, master_df=master_df)

    if filtered_df.empty:
        result = full_divisions.copy()
        result["ha"] = 0.0
        result["crop"] = 0.0
        result["yph"] = 0
        result["estate_avg"] = 0
        result["regional_avg"] = 0
        result["bc"] = 0.0
        result["stand_per_ha"] = 0
        result["lph"] = 0

        result = result.merge(div_extent, on=["estate", "division"], how="left")
        result["div_ext"] = pd.to_numeric(result["div_ext"], errors="coerce").fillna(0)

        result = result.merge(estate_total_ha, on="estate", how="left")
        result["estate_total_ha"] = pd.to_numeric(result["estate_total_ha"], errors="coerce").fillna(0)
    else:
        regional_avg = _regional_avg(filtered_df)
        estate_avg = _estate_avg_table(filtered_df)

        div_stats = (
            filtered_df.groupby(["estate", "division"], dropna=False)
            .apply(
                lambda g: pd.Series(
                    {
                        "ha": _safe_sum(g, "hect"),
                        "crop": _crop_sum(g),
                        "bc": _safe_sum(g, "bc"),
                    }
                )
            )
            .reset_index()
        )

        div_stats["yph"] = div_stats.apply(
            lambda r: _yph_from_crop_ha(float(r["crop"]), float(r["ha"])),
            axis=1,
        )

        div_stats["stand_per_ha"] = div_stats.apply(
            lambda r: int(_round_half_up(float(r["bc"]) / float(r["ha"]))) if float(r["ha"]) > 0 else 0,
            axis=1,
        )

        if is_lc:
            div_stats["lph"] = div_stats["stand_per_ha"].apply(lambda x: _lc_lph(group_name, x))
        else:
            div_stats["lph"] = 0

        result = full_divisions.merge(div_stats, on=["estate", "division"], how="left")
        result["ha"] = pd.to_numeric(result["ha"], errors="coerce").fillna(0)
        result["crop"] = pd.to_numeric(result["crop"], errors="coerce").fillna(0)
        result["bc"] = pd.to_numeric(result["bc"], errors="coerce").fillna(0)
        result["yph"] = pd.to_numeric(result["yph"], errors="coerce").fillna(0).astype(int)
        result["stand_per_ha"] = pd.to_numeric(result["stand_per_ha"], errors="coerce").fillna(0).astype(int)
        result["lph"] = pd.to_numeric(result["lph"], errors="coerce").fillna(0).astype(int)

        result = result.merge(estate_avg, on="estate", how="left")
        result["estate_avg"] = pd.to_numeric(result["estate_avg"], errors="coerce").fillna(0).astype(int)
        result["regional_avg"] = regional_avg

        result = result.merge(div_extent, on=["estate", "division"], how="left")
        result["div_ext"] = pd.to_numeric(result["div_ext"], errors="coerce").fillna(0)

        result = result.merge(estate_total_ha, on="estate", how="left")
        result["estate_total_ha"] = pd.to_numeric(result["estate_total_ha"], errors="coerce").fillna(0)

    if use_estate_pct:
        result["pct"] = result.apply(
            lambda r: int(_round_half_up(float(r["ha"]) / float(r["estate_total_ha"]) * 100)) if float(r["estate_total_ha"]) > 0 else 0,
            axis=1,
        )
        pct_label = "% ESTATE"
    else:
        result["pct"] = result.apply(
            lambda r: int(_round_half_up(float(r["ha"]) / float(r["div_ext"]) * 100)) if float(r["div_ext"]) > 0 else 0,
            axis=1,
        )
        pct_label = "% DIVISION"

    if include_rounds:
        if is_lc:
            kg_per_round = LC_GROUP_PARAMS[group_name]
            result["todate_rounds"] = result.apply(
                lambda r: round(float(r["crop"]) / kg_per_round, 1) if kg_per_round and float(r["ha"]) > 0 else float("nan"),
                axis=1,
            )
            result["rounds_month"] = result["todate_rounds"].apply(
                lambda x: round(float(x) / months_in_period, 1) if pd.notna(x) and months_in_period > 0 else float("nan")
            )
        else:
            params = GROUP_PARAMS[group_name]
            lph, kg_per_round = params
            c = lph * kg_per_round
            result["green_leaf"] = (result["yph"] * GREEN_LEAF_FACTOR).round(0)
            result["todate_rounds"] = result["green_leaf"].apply(
                lambda x: round(float(x) / c, 1) if c > 0 else float("nan")
            )
            result["rounds_month"] = result["green_leaf"].apply(
                lambda x: round(float(x) / months_in_period / c, 1) if months_in_period > 0 and c > 0 else float("nan")
            )
    else:
        result["todate_rounds"] = None
        result["rounds_month"] = None

    benchmark = int(result["yph"].max()) if not result.empty else 0
    for pct in BENCHMARK_PERCENTAGES:
        result[f"bm_{pct}"] = int(_round_half_up(benchmark * pct / 100))

    result["pct_label"] = pct_label
    result["benchmark"] = benchmark
    result["region"] = region

    return result


def build_abstract_summary(
    age_outputs: dict[str, pd.DataFrame],
    vp_output: pd.DataFrame,
    total_output: pd.DataFrame,
) -> pd.DataFrame:
    rows = []

    estate_order = sorted(total_output["estate"].dropna().astype(str).unique().tolist()) if not total_output.empty else []
    base_total_ext = _safe_sum(total_output, "ha")

    def _row_from_processed(year_label: str, dfg: pd.DataFrame, blank_pct_ext: bool = False) -> dict[str, Any]:
        row: dict[str, Any] = {"Year": year_label}

        ext = _safe_sum(dfg, "ha")
        row["Ext"] = round(ext, 2)
        row["% Ext"] = "" if blank_pct_ext else (f"{round(ext / base_total_ext * 100):.0f}%" if base_total_ext > 0 else "0%")

        bench = 0
        for estate in estate_order:
            est_df = dfg[dfg["estate"] == estate] if not dfg.empty else pd.DataFrame()

            ha = _safe_sum(est_df, "ha")
            if not est_df.empty and "estate_avg" in est_df.columns:
                yph = _safe_first_int(est_df["estate_avg"])
            else:
                yph = _yph_from_crop_ha(_safe_sum(est_df, "crop"), ha)

            pct = f"{round(ha / ext * 100):.0f}%" if ext > 0 else "0%"

            row[f"{estate}_YPH"] = yph
            row[f"{estate}_PCT"] = pct
            bench = max(bench, yph)

        row["Benchmark"] = bench
        row["90% BM"] = round(bench * 0.9)
        return row

    for sheet_name in AGE_GROUPS.keys():
        dfg = age_outputs.get(sheet_name, pd.DataFrame())
        rows.append(_row_from_processed(sheet_name, dfg))

    rows.append(_row_from_processed("VP YIELD", vp_output))
    rows.append(_row_from_processed("Total", total_output, blank_pct_ext=True))

    return pd.DataFrame(rows)


def _use_estate_pct_rule(region: str, title: str, default: bool) -> bool:
    region = _canonical_region(region)
    if region == "TTEL_LC":
        return True
    if region in {"KVPL_LC", "HPL_LC"}:
        return False
    return default


def run_report_pipeline(
    region_frames: dict[str, pd.DataFrame],
    selected_month: str,
    master_maps: dict[str, pd.DataFrame] | None = None,
) -> CalculationResult:
    outputs: dict[str, Any] = {}

    year, month = map(int, selected_month.split("-"))
    months_in_period = month - 3 if month >= 4 else month + 9

    master_maps = master_maps or {}

    for region, df in region_frames.items():
        region_key = _canonical_region(region)

        df = _prepare_source_df(df.copy())

        if "sd_vp" not in df.columns:
            df["sd_vp"] = ""

        df["sd_vp"] = df["sd_vp"].astype(str).str.upper().str.strip()

        if "estate" in df.columns:
            df["estate"] = df["estate"].astype(str).str.strip().replace({
                "Great Western": "GreatWestern",
                "GREAT WESTERN": "GreatWestern",
            })

        if "division" in df.columns:
            df["division"] = df["division"].astype(str).str.strip()

        master_df = master_maps.get(region_key)
        if master_df is not None:
            master_df = _prepare_source_df(master_df.copy())

        df = _filter_to_master_pairs(df, master_df)

        vp_df = df[df["sd_vp"] == "VP"].copy()
        sd_df = df[df["sd_vp"] == "SD"].copy()
        total_df = df.copy()

        region_result: dict[str, Any] = {}
        age_outputs: dict[str, pd.DataFrame] = {}

        for title, (a, b) in AGE_GROUPS.items():
            age_df = vp_df[(vp_df["age_months"] >= a) & (vp_df["age_months"] <= b)].copy()
            processed = process_group(
                age_df,
                df,
                title,
                use_estate_pct=_use_estate_pct_rule(region_key, title, False),
                include_rounds=True,
                months_in_period=months_in_period,
                region=region_key,
                master_df=master_df,
            )
            age_outputs[title] = processed
            region_result[title] = processed

        region_result["VP YIELD"] = process_group(
            vp_df,
            df,
            "VP YIELD",
            use_estate_pct=_use_estate_pct_rule(region_key, "VP YIELD", True),
            include_rounds=True,
            months_in_period=months_in_period,
            region=region_key,
            master_df=master_df,
        )

        region_result["SD YIELD"] = process_group(
            sd_df,
            df,
            "SD YIELD",
            use_estate_pct=_use_estate_pct_rule(region_key, "SD YIELD", True),
            include_rounds=True,
            months_in_period=months_in_period,
            region=region_key,
            master_df=master_df,
        )

        region_result["TOTAL (VP + SD) YIELD"] = process_group(
            total_df,
            df,
            "TOTAL (VP + SD) YIELD",
            use_estate_pct=_use_estate_pct_rule(region_key, "TOTAL (VP + SD) YIELD", True),
            include_rounds=False,
            months_in_period=months_in_period,
            region=region_key,
            master_df=master_df,
        )

        region_result["ABSTRACT SUMMARY"] = build_abstract_summary(
            age_outputs=age_outputs,
            vp_output=region_result["VP YIELD"],
            total_output=region_result["TOTAL (VP + SD) YIELD"],
        )

        outputs[region_key] = region_result

    return CalculationResult(selected_month=selected_month, outputs=outputs)