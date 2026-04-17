from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np
import pandas as pd

from app.core.template_config import canonical_region


# ---------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------

REGION_ESTATE_ORDER: dict[str, list[str]] = {
    "TK": ["Bearwell", "Holyrood", "GreatWestern", "Logie", "Mattakelle", "Palmerston", "Wattegoda"],
    "NO": ["Bearwell", "Holyrood", "GreatWestern", "Logie", "Mattakelle", "Palmerston", "Wattegoda"],
    "HT": ["Bearwell", "Holyrood", "GreatWestern", "Logie", "Mattakelle", "Palmerston", "Wattegoda"],
    "NE": ["Bearwell", "Holyrood", "GreatWestern", "Logie", "Mattakelle", "Palmerston", "Wattegoda"],
    "UC": ["Bearwell", "Holyrood", "GreatWestern", "Logie", "Mattakelle", "Palmerston", "Wattegoda"],
    "LD": ["Bearwell", "Holyrood", "GreatWestern", "Logie", "Mattakelle", "Palmerston", "Wattegoda"],
    "TTEL_LC": ["Bearwell", "Holyrood", "GreatWestern", "Logie", "Mattakelle", "Palmerston", "Wattegoda"],
    "KVPL_LC": ["Bearwell", "Holyrood", "GreatWestern", "Logie", "Mattakelle", "Palmerston", "Wattegoda"],
    "HPL_LC": ["Bearwell", "Holyrood", "GreatWestern", "Logie", "Mattakelle", "Palmerston", "Wattegoda"],
}

DEFAULT_PALETTE = [
    "#d95f57",  # red
    "#d3ca55",  # mustard
    "#71d34f",  # green
    "#58cfa0",  # teal
    "#5a95d1",  # blue
    "#8257d2",  # purple
    "#d056c0",  # magenta
]

FIXED_ESTATE_COLORS = {
    "Bearwell": "#d95f57",
    "Holyrood": "#d3ca55",
    "GreatWestern": "#71d34f",
    "Logie": "#58cfa0",
    "Mattakelle": "#5a95d1",
    "Palmerston": "#8257d2",
    "Wattegoda": "#d056c0",
}

TITLE_META = {
    "1-12 MONTHS": {"red_title": "1$^{st}$ YEAR", "rounds_note": "NUMBER OF ROUNDS @ 11 LPH @ 20 kg"},
    "13-24 MONTHS": {"red_title": "2$^{nd}$ YEAR", "rounds_note": "NUMBER OF ROUNDS @ 11 LPH @ 20 kg"},
    "25-36 MONTHS": {"red_title": "3$^{rd}$ YEAR", "rounds_note": "NUMBER OF ROUNDS @ 11 LPH @ 20 kg"},
    "37-48 MONTHS": {"red_title": "4$^{th}$ YEAR", "rounds_note": "NUMBER OF ROUNDS @ 11 LPH @ 20 kg"},
    "48+ MONTHS": {"red_title": "5$^{th}$ YEAR", "rounds_note": "NUMBER OF ROUNDS @ 11 LPH @ 20 kg"},
    "VP YIELD": {"red_title": "VP", "rounds_note": "NUMBER OF ROUNDS @ 11 LPH @ 20 kg"},
    "SD YIELD": {"red_title": "SD", "rounds_note": "NUMBER OF ROUNDS @ 11 LPH @ 20 kg"},
    "TOTAL (VP + SD) YIELD": {"red_title": "TOTAL", "rounds_note": "NUMBER OF ROUNDS @ 11 LPH @ 20 kg"},
}

LEGACY_GRAPH_NAMES = {
    "1-12 MONTHS": "Graph 1",
    "13-24 MONTHS": "Graph 2",
    "25-36 MONTHS": "Graph 3",
    "37-48 MONTHS": "Graph 4",
    "48+ MONTHS": "Graph 5",
    "VP YIELD": "Graph VP",
    "SD YIELD": "Graph SD",
    "TOTAL (VP + SD) YIELD": "Graph Tot",
}

LEGACY_SIZE_SPECS = {
    "TK": {
        "__default__": (1244, 711),
        "_with_inset_right": (1244, 711),
        "Graph 1_with_inset_right": (1244, 711),
        "Graph 2_with_inset_right": (1244, 711),
        "Graph 3_with_inset_right": (1244, 711),
        "Graph 4_with_inset_right": (1244, 711),
        "Graph 5_with_inset_right": (1244, 711),
        "Graph VP_with_inset_right": (1244, 711),
        "Graph Tot_with_inset_right": (1244, 711),
    },
    "NE": {
        "__default__": (1244, 711),
        "_with_inset_right": (1244, 711),
    },
    "HT": {
        "__default__": (1244, 711),
        "_with_inset_right": (1244, 711),
    },
}


REGION_DISPLAY_NAMES = {
    "TK": "Talawakelle Region",
    "NO": "Nanu Oya Region",
    "TTEL_LC": "Talawakelle Low Country Region",
    "NE": "Nuwara Eliya",
    "HT": "Hatton",
    "KVPL_LC": "Kelani Valley Low Country - Tea",
    "UC": "UPCOT",
    "LD": "Lindula",
    "HPL_LC": "Horana Low Country - Tea",
}

# ---------------------------------------------------------------------
# BASIC HELPERS
# ---------------------------------------------------------------------

def _canonical_region(region: str) -> str:
    return canonical_region(region)


def _display_region(region: str) -> str:
    region = _canonical_region(region)
    return REGION_DISPLAY_NAMES.get(region, region.replace("_", " - "))


def _is_lc_region(region: str) -> bool:
    return "LC" in _canonical_region(region)


def _palette_for_region(region: str) -> list[str]:
    return DEFAULT_PALETTE


def _fixed_color_lookup(region: str) -> dict[str, str]:
    return FIXED_ESTATE_COLORS


def _normalize_sheet_title(title: str) -> str:
    t = str(title).strip().upper()
    aliases = {
        "1ST YEAR VP YIELD": "1-12 MONTHS",
        "2ND YEAR VP YIELD": "13-24 MONTHS",
        "3RD YEAR VP YIELD": "25-36 MONTHS",
        "4TH YEAR VP YIELD": "37-48 MONTHS",
        "5TH YEAR VP YIELD": "48+ MONTHS",
        "1ST YEAR": "1-12 MONTHS",
        "2ND YEAR": "13-24 MONTHS",
        "3RD YEAR": "25-36 MONTHS",
        "4TH YEAR": "37-48 MONTHS",
        "5TH YEAR": "48+ MONTHS",
        "VP": "VP YIELD",
        "SD": "SD YIELD",
        "TOTAL": "TOTAL (VP + SD) YIELD",
    }
    return aliases.get(t, title)


def _legacy_graph_label(title: str) -> str:
    title = _normalize_sheet_title(title)
    return LEGACY_GRAPH_NAMES.get(title, "Graph")


def _sheet_slug(title: str) -> str:
    return (
        str(title).lower()
        .replace("(", "")
        .replace(")", "")
        .replace("+", "plus")
        .replace("&", "and")
        .replace("/", "_")
        .replace(" ", "_")
    )


def _clean_code_series(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip()


def _title_info(title: str, region: str) -> tuple[list[str], str]:
    title = _normalize_sheet_title(title)
    meta = TITLE_META.get(title, {"red_title": title, "rounds_note": None})
    display_region = _display_region(region)
    lines = [f"TEA - VP YPH - {display_region} - DIVISIONAL YIELD - {title}"]
    return lines, meta["red_title"]


def _lc_round_note(df_main: pd.DataFrame, title: str) -> str:
    return "NUMBER OF ROUNDS @ 11 LPH @ 20 kg"


def _apply_common_axis_style(ax):
    ax.set_facecolor("white")
    for spine in ax.spines.values():
        spine.set_color("#222222")
        spine.set_linewidth(0.9)
    ax.grid(axis="y", color="#dddddd", linewidth=0.7, linestyle="-", alpha=0.65)
    ax.tick_params(axis="both", labelsize=8, colors="#333333")
    ax.set_axisbelow(True)


def set_nice_yticks(ax, max_y: float):
    max_y = max(float(max_y), 100.0)
    top = int(np.ceil(max_y / 250.0) * 250.0)
    ax.set_ylim(0, top * 1.05)
    ax.yaxis.set_major_locator(MaxNLocator(nbins=6, integer=True))


def _bar_geometry(count: int, *, inset: bool = False, thin: bool = False) -> tuple[float, float]:
    """Return bar width and outer x-padding.

    Use slimmer bars only for single-estate charts like Millakanda.
    Keep multi-estate regional charts on the original, fuller look.
    """
    count = max(int(count), 1)

    if not thin:
        return (0.55, 0.0) if inset else (0.58, 0.0)

    if inset:
        if count <= 3:
            return 0.40, 0.18
        if count <= 5:
            return 0.34, 0.15
        if count <= 8:
            return 0.30, 0.12
        return 0.26, 0.10

    if count <= 3:
        return 0.30, 0.20
    if count <= 5:
        return 0.28, 0.16
    if count <= 8:
        return 0.24, 0.12
    return 0.20, 0.10


def _numeric_series(df: pd.DataFrame, candidates: list[str], default: float = 0.0) -> pd.Series:
    if df.empty:
        return pd.Series(dtype=float)

    for col in candidates:
        if col in df.columns:
            s = df[col]
            if s.dtype == object:
                s = s.astype(str).str.replace("%", "", regex=False).str.replace(",", "", regex=False).str.strip()
            out = pd.to_numeric(s, errors="coerce").fillna(default)
            return out.astype(float)

    return pd.Series([default] * len(df), index=df.index, dtype=float)


def _format_num(val: float | int, digits: int = 0) -> str:
    if digits == 0:
        return f"{int(round(float(val)))}"
    return f"{float(val):.{digits}f}"


def get_estate_order(df: pd.DataFrame, region: str) -> list[str]:
    region = _canonical_region(region)
    configured = REGION_ESTATE_ORDER.get(region, [])

    if "estate" not in df.columns:
        return configured or []

    present = df["estate"].dropna().astype(str).str.strip().tolist()
    present_unique: list[str] = []
    seen: set[str] = set()

    for e in present:
        if e and e not in seen:
            seen.add(e)
            present_unique.append(e)

    if configured:
        ordered = [e for e in configured if e in present_unique]
        remaining = [e for e in present_unique if e not in ordered]
        return ordered + sorted(remaining)

    return sorted(present_unique)


def get_estate_colors(estate_order: list[str], region: str) -> dict[str, str]:
    colors: dict[str, str] = {}
    palette = _palette_for_region(region)
    fixed = _fixed_color_lookup(region)
    next_idx = 0

    for estate in estate_order:
        if estate in fixed:
            colors[estate] = fixed[estate]
        else:
            colors[estate] = palette[next_idx % len(palette)]
            next_idx += 1

    return colors


def _sort_for_main(df: pd.DataFrame, estate_order: list[str]) -> pd.DataFrame:
    if df.empty or "estate" not in df.columns or "yph" not in df.columns:
        return df.copy()

    parts: list[pd.DataFrame] = []
    for estate in estate_order:
        sub = df[df["estate"] == estate].copy()
        if not sub.empty:
            sub["__yph__"] = pd.to_numeric(sub["yph"], errors="coerce").fillna(0)
            sub = sub.sort_values("__yph__").drop(columns="__yph__")
            parts.append(sub)

    return pd.concat(parts, ignore_index=True) if parts else df.copy()


def _sort_desc(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "yph" not in df.columns:
        return df.copy()

    out = df.copy()
    out["__yph__"] = pd.to_numeric(out["yph"], errors="coerce").fillna(0)
    out = out.sort_values("__yph__", ascending=False).drop(columns="__yph__").reset_index(drop=True)
    return out


# ---------------------------------------------------------------------
# TABLE FORMATTING
# ---------------------------------------------------------------------

def _format_table_rows(df_main: pd.DataFrame, title: str, is_lc: bool) -> tuple[list[str], list[list[str]]]:
    if df_main.empty:
        if is_lc:
            return (
                ["YPH (kg/ha)", "% DIVISION", "BC", "STAND/HA", "LPH"],
                [["0"], ["0%"], ["0"], ["0"], ["0"]],
            )
        return (
            ["YPH (kg/ha)", "% DIVISION", "TODATE ROUNDS", "ROUNDS @ MONTH"],
            [["0"], ["0%"], ["0"], ["0"]],
        )

    yph = _numeric_series(df_main, ["yph", "YPH"])
    pct = _numeric_series(df_main, ["percent", "pct_division", "% DIVISION", "% Division", "Division%", "division_pct"])

    if is_lc:
        bc = _numeric_series(df_main, ["bc", "BC"])
        stand_ha = _numeric_series(df_main, ["stand_per_ha", "stand/ha", "STAND/HA", "Stand/Ha"])
        lph = _numeric_series(df_main, ["lph", "LPH"])

        row_labels = ["YPH (kg/ha)", "% DIVISION", "BC", "STAND/HA", "LPH"]
        data_rows = [
            [_format_num(v) for v in yph],
            [f"{int(round(v))}%" for v in pct],
            [_format_num(v) for v in bc],
            [_format_num(v) for v in stand_ha],
            [_format_num(v, 1) for v in lph],
        ]
        return row_labels, data_rows

    todate_rounds = _numeric_series(df_main, ["todate_rounds", "TODATE ROUNDS", "rounds", "ROUNDS"])
    rounds_month = _numeric_series(df_main, ["rounds_month", "ROUNDS @ MONTH", "rounds @ month"])

    row_labels = ["YPH (kg/ha)", "% DIVISION", "TODATE ROUNDS", "ROUNDS @ MONTH"]
    data_rows = [
        [_format_num(v) for v in yph],
        [f"{int(round(v))}%" for v in pct],
        [_format_num(v, 1) for v in todate_rounds],
        [_format_num(v, 1) for v in rounds_month],
    ]
    return row_labels, data_rows


def _render_aligned_table(fig, main_pos, df_main: pd.DataFrame, title: str, is_lc: bool):
    row_labels, data_rows = _format_table_rows(df_main, title, is_lc)
    col_labels = df_main["code"].tolist() if not df_main.empty and "code" in df_main.columns else ["NA"]

    if not data_rows:
        data_rows = [["0"] * len(col_labels) for _ in row_labels]

    n_cols = max(len(col_labels), 1)
    n_rows = len(row_labels) + 1

    main_left, main_bottom, main_width, _ = main_pos

    label_width = 0.105 if not is_lc else 0.120
    table_gap = 0.004

    row_height = 0.040 if not is_lc else 0.034
    table_height = max(0.160 if not is_lc else 0.230, n_rows * row_height)
    table_bottom = max(0.02, main_bottom - table_height - table_gap)

    label_left = max(0.01, main_left - label_width)

    ax_labels = fig.add_axes([label_left, table_bottom, label_width, table_height])
    ax_labels.axis("off")

    ax_table = fig.add_axes([main_left, table_bottom, main_width, table_height])
    ax_table.axis("off")

    label_cell_text = [[""]] + [[label] for label in row_labels]
    label_tbl = ax_labels.table(
        cellText=label_cell_text,
        colWidths=[1.0],
        cellLoc="left",
        bbox=[0.0, 0.0, 1.0, 1.0],
    )
    label_tbl.auto_set_font_size(False)
    label_tbl.set_fontsize(10.0 if not is_lc else 8.6)

    body_text = [col_labels] + data_rows
    col_widths = [1.0 / n_cols] * n_cols
    body_tbl = ax_table.table(
        cellText=body_text,
        colWidths=col_widths,
        cellLoc="center",
        bbox=[0.0, 0.0, 1.0, 1.0],
    )
    body_tbl.auto_set_font_size(False)
    body_tbl.set_fontsize(9.7 if not is_lc else 8.3)

    edge_color = "#202020"
    header_face = "#f1f1f1"
    body_face = "white"
    uniform_cell_h = 1.0 / n_rows

    for (row, col), cell in label_tbl.get_celld().items():
        cell.set_edgecolor(edge_color)
        cell.set_linewidth(0.95)
        cell.set_facecolor(header_face if row == 0 else body_face)
        cell.set_height(uniform_cell_h)
        cell.PAD = 0.06
        cell.get_text().set_fontfamily("serif")
        cell.get_text().set_ha("left")
        cell.get_text().set_va("center")
        cell.get_text().set_fontweight("bold" if row > 0 else "normal")
        if row == 0:
            cell.get_text().set_text("")

    for (row, col), cell in body_tbl.get_celld().items():
        cell.set_edgecolor(edge_color)
        cell.set_linewidth(0.95)
        cell.set_facecolor(header_face if row == 0 else body_face)
        cell.set_height(uniform_cell_h)
        cell.PAD = 0.03
        cell.get_text().set_fontfamily("serif")
        cell.get_text().set_ha("center")
        cell.get_text().set_va("center")
        cell.get_text().set_fontweight("bold" if row == 0 else "normal")

    return table_bottom, table_height


# ---------------------------------------------------------------------
# FILE OUTPUT
# ---------------------------------------------------------------------

def save_legacy_chart_variants(fig, output_dir: str, region: str, title: str, stem: str) -> dict[str, str | None]:
    region = _canonical_region(region)
    region_dir = Path(output_dir)
    preview_png = region_dir / "preview_png"
    preview_jpg = region_dir / "preview_jpg"
    preview_svg = region_dir / "preview_svg"
    vp_dir = region_dir / "VP"

    for d in (preview_png, preview_jpg, preview_svg, vp_dir):
        d.mkdir(parents=True, exist_ok=True)

    png_path = preview_png / f"{stem}.png"
    jpg_path = preview_jpg / f"{stem}.jpg"
    svg_path = preview_svg / f"{stem}.svg"

    fig.savefig(png_path, dpi=100, facecolor="white", bbox_inches=None)
    fig.savefig(jpg_path, dpi=100, facecolor="white", bbox_inches=None)
    fig.savefig(svg_path, facecolor="white", bbox_inches=None)

    legacy_base = _legacy_graph_label(title)
    legacy_jpg = vp_dir / f"{legacy_base}.jpg"
    legacy_png = vp_dir / f"{legacy_base}.png"

    fig.savefig(legacy_jpg, dpi=100, facecolor="white", bbox_inches=None)
    fig.savefig(legacy_png, dpi=100, facecolor="white", bbox_inches=None)

    if region in {"TK", "NE", "HT"}:
        inset_name_jpg = vp_dir / f"{legacy_base}_with_inset_right.jpg"
        inset_name_png = vp_dir / f"{legacy_base}_with_inset_right.png"
        fig.savefig(inset_name_jpg, dpi=100, facecolor="white", bbox_inches=None)
        fig.savefig(inset_name_png, dpi=100, facecolor="white", bbox_inches=None)

    return {
        "png": str(png_path),
        "jpg": str(jpg_path),
        "svg": str(svg_path),
        "legacy_jpg": str(legacy_jpg),
        "legacy_png": str(legacy_png),
    }


# ---------------------------------------------------------------------
# MAIN RENDERER
# ---------------------------------------------------------------------

def render_chart(
    df: pd.DataFrame,
    region: str,
    title: str,
    selected_month: str,
    output_dir: str,
) -> str:
    region = _canonical_region(region)
    title = _normalize_sheet_title(title)

    estate_order = get_estate_order(df, region)
    estate_colors = get_estate_colors(estate_order, region)

    df_main = _sort_for_main(df, estate_order).copy()
    df_desc = _sort_desc(df).copy()

    single_estate_chart = False
    if not df_main.empty and "estate" in df_main.columns:
        single_estate_chart = df_main["estate"].nunique(dropna=True) == 1

    if "code" in df_main.columns:
        df_main["code"] = _clean_code_series(df_main["code"])
    if "code" in df_desc.columns:
        df_desc["code"] = _clean_code_series(df_desc["code"])

    if "code" in df_main.columns:
        df_main = df_main[df_main["code"] != ""].reset_index(drop=True)
    if "code" in df_desc.columns:
        df_desc = df_desc[df_desc["code"] != ""].reset_index(drop=True)

    if not df.empty and "benchmark" in df.columns:
        benchmark = int(_numeric_series(df, ["benchmark"]).iloc[0])
    else:
        yph_for_bm = _numeric_series(df, ["yph", "YPH"])
        benchmark = int(yph_for_bm.max()) if not yph_for_bm.empty else 0

    bm80 = round(benchmark * 0.8)
    bm70 = round(benchmark * 0.7)
    bm50 = round(benchmark * 0.5)

    year, month = map(int, selected_month.split("-"))
    start_year = year if month >= 4 else year - 1
    period_months = month - 3 if month >= 4 else month + 9

    if _is_lc_region(region):
        date_line = f"01-04-{start_year} TO 31-{month:02d}-{year} ({period_months} MONTHS)"
    else:
        date_line = f"(01-04-{start_year} TO 31-{month:02d}-{year}) - {period_months} MONTHS"

    title_lines, red_title = _title_info(title, region)
    title_lines.append(date_line)

    if _is_lc_region(region):
        rounds_note = _lc_round_note(df_main, title)
    else:
        rounds_note = TITLE_META.get(title, {}).get("rounds_note")
    if rounds_note:
        title_lines.append(rounds_note)

    graph_label = _legacy_graph_label(title)
    canvas_w, canvas_h = (
        LEGACY_SIZE_SPECS.get(region, {}).get(f"{graph_label}_with_inset_right")
        or LEGACY_SIZE_SPECS.get(region, {}).get("_with_inset_right")
        or LEGACY_SIZE_SPECS.get(region, {}).get(graph_label)
        or LEGACY_SIZE_SPECS.get(region, {}).get("__default__")
        or (1244, 711)
    )

    dpi = 100
    fig = plt.figure(figsize=(canvas_w / dpi, canvas_h / dpi), dpi=dpi)
    fig.patch.set_facecolor("white")

    font_stack = ["Times New Roman", "Liberation Serif", "DejaVu Serif", "serif"]
    matplotlib.rcParams["font.family"] = "serif"
    matplotlib.rcParams["font.serif"] = font_stack

    # Clean header layout like reference
    title_pos = [0.05, 0.82, 0.43, 0.13]
    desc_pos = [0.53, 0.69, 0.40, 0.23]
    red_title_xy = (0.090, 0.700)

    is_lc = _is_lc_region(region)
    if title == "TOTAL (VP + SD) YIELD":
        main_pos = [0.115, 0.22, 0.835, 0.40]
    elif is_lc:
        main_pos = [0.115, 0.33, 0.835, 0.31]
    else:
        main_pos = [0.115, 0.215, 0.835, 0.43]

    ax_title = fig.add_axes(title_pos)
    ax_title.axis("off")
    ax_title.text(
        0.0,
        1.0,
        "\n".join(title_lines),
        va="top",
        ha="left",
        fontsize=16 if not is_lc else 14,
        fontweight="bold",
        family="serif",
        linespacing=1.10,
        color="black",
    )

    ax_desc = fig.add_axes(desc_pos)
    _apply_common_axis_style(ax_desc)
    if not df_desc.empty:
        x_desc = np.arange(len(df_desc), dtype=float)
        desc_y = _numeric_series(df_desc, ["yph", "YPH"])
        desc_colors = [estate_colors.get(est, "#888888") for est in df_desc["estate"]]
        desc_bar_width, desc_pad = _bar_geometry(len(df_desc), inset=True, thin=single_estate_chart)
        ax_desc.bar(
            x_desc,
            desc_y,
            color=desc_colors,
            width=desc_bar_width,
            edgecolor="#ffffff" if single_estate_chart else "none",
            linewidth=0.8 if single_estate_chart else 0.0,
            alpha=0.95,
        )
        ax_desc.set_xlim(-0.5 - desc_pad, len(df_desc) - 0.5 + desc_pad)
        ax_desc.set_xticks(x_desc)
        ax_desc.set_xticklabels(df_desc["code"].tolist(), rotation=90, fontsize=7, family="serif")
    else:
        ax_desc.set_xticks([])

    ax_desc.axhline(bm80, color="#e59f00", linestyle="--", linewidth=1.8)
    ax_desc.axhline(bm70, color="green", linestyle="--", linewidth=1.8)
    ax_desc.axhline(bm50, color="red", linestyle="--", linewidth=1.8)
    desc_max = float(_numeric_series(df_desc, ["yph", "YPH"]).max()) if not df_desc.empty else max(benchmark, 1000)
    set_nice_yticks(ax_desc, desc_max)
    ax_desc.set_title("DESCENDING ORDER", fontsize=15, fontweight="bold", family="serif", pad=4)

    fig.text(
        red_title_xy[0],
        red_title_xy[1],
        red_title,
        color="red",
        fontsize=21 if not is_lc else 20,
        fontweight="bold",
        family="serif",
        ha="left",
        va="center",
    )

    ax = fig.add_axes(main_pos)
    _apply_common_axis_style(ax)

    if df_main.empty:
        x_positions = np.array([0.0])
        main_bar_width, main_pad = _bar_geometry(1, thin=single_estate_chart)
        ax.bar(x_positions, [0], color="#cccccc", width=main_bar_width)
        ax.set_xlim(-0.5 - main_pad, 0.5 + main_pad)
    else:
        x_positions = np.arange(len(df_main), dtype=float)
        y_main = _numeric_series(df_main, ["yph", "YPH"])
        bar_colors = [estate_colors.get(est, "#888888") for est in df_main["estate"]]
        main_bar_width, main_pad = _bar_geometry(len(df_main), thin=single_estate_chart)
        ax.bar(
            x_positions,
            y_main,
            color=bar_colors,
            width=main_bar_width,
            edgecolor="#ffffff" if single_estate_chart else "none",
            linewidth=1.0 if single_estate_chart else 0.0,
            alpha=0.96,
        )
        ax.set_xlim(-0.5 - main_pad, len(df_main) - 0.5 + main_pad)

        for estate in estate_order:
            sub = df_main[df_main["estate"] == estate]
            if sub.empty:
                continue
            idxs = sub.index.to_list()
            group_pad = max(main_bar_width / 2.0 + 0.04, 0.12) if single_estate_chart else 0.42
            start = idxs[0] - group_pad
            end = idxs[-1] + group_pad
            avg_val = float(_numeric_series(sub, ["estate_avg", "Estate_Avg"]).iloc[0]) if not sub.empty else 0.0
            ax.hlines(avg_val, start, end, colors="black", linewidth=1.6)
            label_x = (idxs[0] + idxs[-1]) / 2.0
            ax.text(
                label_x,
                avg_val + max(8, benchmark * 0.002),
                f"{int(round(avg_val))}",
                ha="center",
                va="bottom",
                fontsize=10 if not is_lc else 8.5,
                fontweight="bold",
                family="serif",
                color="black",
            )

    ax.axhline(bm80, color="#e59f00", linestyle="--", linewidth=2.0)
    ax.axhline(bm70, color="green", linestyle="--", linewidth=2.0)
    ax.axhline(bm50, color="red", linestyle="--", linewidth=2.0)

    label_x = -0.33
    ax.text(label_x, bm80 + 10, f"80% = {bm80}", color="#d14e00", fontsize=11, fontweight="bold", family="serif")
    ax.text(label_x, bm70 + 10, f"70% = {bm70}", color="green", fontsize=11, fontweight="bold", family="serif")
    ax.text(label_x, bm50 + 10, f"50% = {bm50}", color="red", fontsize=11, fontweight="bold", family="serif")

    main_max = float(_numeric_series(df_main, ["yph", "YPH"]).max()) if not df_main.empty else max(benchmark, 1000)
    set_nice_yticks(ax, main_max)

    ax.set_xticks([])
    ax.tick_params(axis="x", length=0)

    handles = []
    labels = []
    present_estates = set(df_main["estate"].tolist()) if not df_main.empty and "estate" in df_main.columns else set()
    for estate in estate_order:
        if estate in present_estates:
            handles.append(plt.Rectangle((0, 0), 1, 1, color=estate_colors.get(estate, "#888888"), ec="none"))
            labels.append(estate)

    if handles:
        leg = ax.legend(
            handles,
            labels,
            loc="upper left",
            bbox_to_anchor=(0.002, 1.002, 0.998, 0.0),
            mode="expand",
            ncol=len(handles),
            frameon=True,
            fontsize=8.2,
            borderpad=0.30,
            handlelength=1.7,
            handletextpad=0.40,
            columnspacing=0.8,
            labelspacing=0.45,
            borderaxespad=0.25,
        )
        leg.get_frame().set_facecolor("white")
        leg.get_frame().set_edgecolor("#c9c9c9")
        for txt_obj in leg.get_texts():
            txt_obj.set_family("serif")

    _render_aligned_table(fig, main_pos, df_main, title, is_lc)

    stem = f"{region.lower()}_{_sheet_slug(title)}"
    saved = save_legacy_chart_variants(fig, output_dir, region, title, stem)
    plt.close(fig)
    return str(saved["jpg"] or saved["png"])
