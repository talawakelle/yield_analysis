from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


matplotlib.rcParams.update({
    "figure.dpi": 240,
    "savefig.dpi": 320,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "text.antialiased": True,
    "lines.antialiased": True,
    "patch.antialiased": True,
})


REGION_ALIASES = {
    "LC": "TTEL_LC",
    "RB": "HT",
}


def _canonical_region(region: str) -> str:
    return REGION_ALIASES.get(str(region).strip().upper(), str(region).strip().upper())


def save_figure_ultra(fig, output_dir: str, stem: str, make_jpg: bool = True) -> dict[str, str | None]:
    base_dir = Path(output_dir)
    png_dir = base_dir / "preview_png"
    jpg_dir = base_dir / "preview_jpg"
    svg_dir = base_dir / "preview_svg"

    png_dir.mkdir(parents=True, exist_ok=True)
    jpg_dir.mkdir(parents=True, exist_ok=True)
    svg_dir.mkdir(parents=True, exist_ok=True)

    png_path = png_dir / f"{stem}.png"
    jpg_path = jpg_dir / f"{stem}.jpg"
    svg_path = svg_dir / f"{stem}.svg"

    fig.savefig(
        png_path,
        format="png",
        dpi=320,
        bbox_inches="tight",
        pad_inches=0.20,
        facecolor=fig.get_facecolor(),
        edgecolor="none",
    )
    fig.savefig(
        svg_path,
        format="svg",
        bbox_inches="tight",
        pad_inches=0.20,
        facecolor=fig.get_facecolor(),
        edgecolor="none",
    )

    result: dict[str, str | None] = {"png": str(png_path), "jpg": None, "svg": str(svg_path)}

    if make_jpg:
        fig.savefig(
            jpg_path,
            format="jpg",
            dpi=320,
            bbox_inches="tight",
            pad_inches=0.20,
            facecolor="white",
            edgecolor="none",
            pil_kwargs={
                "quality": 100,
                "subsampling": 0,
                "optimize": False,
            },
        )
        result["jpg"] = str(jpg_path)

    return result


def _sheet_slug(title: str) -> str:
    return (
        title.lower()
        .replace("(", "")
        .replace(")", "")
        .replace("+", "plus")
        .replace("&", "and")
        .replace(" ", "_")
    )


def _display_year(value: str) -> str:
    mapping = {
        "1st YEAR VP YIELD": "1st Year",
        "2nd YEAR VP YIELD": "2nd Year",
        "3rd YEAR VP YIELD": "3rd Year",
        "4th YEAR VP YIELD": "4th Year",
        "5th YEAR VP YIELD": "5th Year",
        "VP YIELD": "Overall VP",
        "Total": "Total",
    }
    return mapping.get(value, value)


def _rename_columns_for_display(df: pd.DataFrame) -> pd.DataFrame:
    display_df = df.copy()

    rename_map = {}
    for col in display_df.columns:
        if col.endswith("_YPH"):
            rename_map[col] = col.replace("_YPH", "")
        elif col.endswith("_PCT"):
            rename_map[col] = col.replace("_PCT", " % EXT")

    display_df = display_df.rename(columns=rename_map)

    if "Year" in display_df.columns:
        display_df["Year"] = display_df["Year"].map(_display_year).fillna(display_df["Year"])

    return display_df


def _build_display_headers(display_df: pd.DataFrame):
    cols = [str(c).strip() for c in display_df.columns.tolist()]

    top_headers = []
    sub_headers = []

    fixed_prefix = {"Year", "Ext", "% Ext"}
    fixed_suffix = {"Benchmark", "90% BM"}

    i = 0
    while i < len(cols):
        col = cols[i]

        if col in fixed_prefix or col in fixed_suffix:
            top_headers.append(col)
            sub_headers.append("")
            i += 1
            continue

        if i + 1 < len(cols):
            next_col = cols[i + 1]
            if str(next_col).strip() == f"{col} % EXT":
                top_headers.extend([col, col])
                sub_headers.extend(["YPH", "% EXT"])
                i += 2
                continue

        top_headers.append(col)
        sub_headers.append("")
        i += 1

    return top_headers, sub_headers


def render_abstract_summary(
    df: pd.DataFrame,
    region: str,
    output_dir: str,
) -> str:
    region = _canonical_region(region)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    display_df = _rename_columns_for_display(df)
    top_headers, sub_headers = _build_display_headers(display_df)

    fig, ax = plt.subplots(figsize=(30, 12), dpi=220)
    fig.patch.set_facecolor("#efefef")
    ax.axis("off")

    cell_text = [sub_headers] + display_df.values.tolist()

    table = ax.table(
        cellText=cell_text,
        colLabels=top_headers,
        cellLoc="center",
        colLoc="center",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.08, 2.15)

    for (r, c), cell in table.get_celld().items():
        cell.set_linewidth(1.0)
        cell.set_edgecolor("black")

        if r == 0:
            cell.set_facecolor("#e6e6e6")
            cell.set_text_props(weight="bold", family="serif", fontsize=10)
        elif r == 1:
            cell.set_facecolor("#e6e6e6")
            cell.set_text_props(weight="bold", family="serif", fontsize=9.5)
        else:
            cell.set_text_props(family="serif", fontsize=9)

    fixed_vertical = {"Year", "Ext", "% Ext", "Benchmark", "90% BM"}
    for c, name in enumerate(top_headers):
        if name in fixed_vertical:
            table[(0, c)].visible_edges = "TLR"
            table[(1, c)].visible_edges = "LBR"
            table[(1, c)].get_text().set_text("")

    c = 0
    while c < len(top_headers) - 1:
        if top_headers[c] == top_headers[c + 1] and sub_headers[c] == "YPH" and sub_headers[c + 1] == "% EXT":
            table[(0, c)].visible_edges = "TLB"
            table[(0, c + 1)].visible_edges = "TRB"
            table[(0, c + 1)].get_text().set_text("")
            c += 2
        else:
            c += 1

    real_cols = display_df.columns.tolist()
    col_index = {name: idx for idx, name in enumerate(real_cols)}

    benchmark_idx = col_index.get("Benchmark")
    bm90_idx = col_index.get("90% BM")

    estate_yph_cols = []
    for col in real_cols:
        if col in {"Year", "Ext", "% Ext", "Benchmark", "90% BM"}:
            continue
        if str(col).endswith(" % EXT"):
            continue
        estate_yph_cols.append(col)

    for data_row_idx in range(len(display_df)):
        table_row_idx = data_row_idx + 2

        benchmark_val = None
        bm90_val = None

        try:
            if benchmark_idx is not None:
                benchmark_val = float(display_df.iloc[data_row_idx, benchmark_idx])
        except Exception:
            benchmark_val = None

        try:
            if bm90_idx is not None:
                bm90_val = float(display_df.iloc[data_row_idx, bm90_idx])
        except Exception:
            bm90_val = None

        if benchmark_idx is not None and benchmark_val is not None:
            table[(table_row_idx, benchmark_idx)].set_facecolor("#f3d4b3")

        for col_name in estate_yph_cols:
            cidx = col_index[col_name]

            try:
                val = float(display_df.iloc[data_row_idx, cidx])
            except Exception:
                continue

            if benchmark_val is not None and val == benchmark_val:
                table[(table_row_idx, cidx)].set_facecolor("#f3d4b3")
            elif bm90_val is not None and val >= bm90_val:
                table[(table_row_idx, cidx)].set_facecolor("#cdeecb")

    fig.text(
        0.5,
        0.02,
        "Peach - Benchmark | Green - YPH Greater than 90% of Benchmark",
        ha="center",
        va="bottom",
        fontsize=12,
        fontweight="bold",
        family="serif",
    )

    stem = f"{region.lower()}_{_sheet_slug('ABSTRACT SUMMARY')}"
    saved = save_figure_ultra(fig, str(out_dir), stem, make_jpg=True)
    plt.close(fig)
    return str(saved["png"])