from __future__ import annotations

from io import BytesIO
from typing import Optional
import pandas as pd


COLUMN_ALIASES = {
    "estate": ["ESTATE", "Estate", "estate"],
    "division": ["DIVISION", "Division", "division"],
    "field_no": ["FieldNo", "F/NO", "Field No", "FIELDNO", "fieldno", "FIELD NO", "Field_No"],
    "bc": ["BC", "Bc", "bc"],
    "age_months": ["AGE", "Age", "age", "Age Months", "AGE MONTHS"],
    "sd_vp": ["SD/VP", "VPSD", "sd/vp", "vpsd", "SD VP", "VP/SD"],
    "hect": ["HECT", "Hect", "Extent", "hect", "extent", "HECTARES"],
    "crop": ["Crop", "CROP", "crop"],
    "yph": ["YPH", "Todate YPH", "To date YPH", " YPH ", "yph", "todate yph", "to date yph"],
}

SHEET_PRIORITY = [
    "Sheet1",
    "Sheet 1",
    "Data",
]


def _clean_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_column_lookup(columns: list[object]) -> dict[str, object]:
    lookup: dict[str, object] = {}
    for col in columns:
        key = _clean_text(col).lower()
        lookup[key] = col
    return lookup


def _find_column(df: pd.DataFrame, aliases: list[str]) -> Optional[object]:
    lookup = _normalize_column_lookup(list(df.columns))
    for alias in aliases:
        key = alias.strip().lower()
        if key in lookup:
            return lookup[key]
    return None


def _score_sheet(df: pd.DataFrame) -> int:
    score = 0
    for aliases in COLUMN_ALIASES.values():
        if _find_column(df, aliases) is not None:
            score += 1
    return score


def _pick_best_sheet(excel: pd.ExcelFile, file_bytes: bytes) -> str:
    for sheet_name in SHEET_PRIORITY:
        if sheet_name in excel.sheet_names:
            return sheet_name

    best_sheet = excel.sheet_names[0]
    best_score = -1

    for sheet_name in excel.sheet_names:
        try:
            df = pd.read_excel(BytesIO(file_bytes), sheet_name=sheet_name)
            score = _score_sheet(df)
            if score > best_score:
                best_score = score
                best_sheet = sheet_name
        except Exception:
            continue

    return best_sheet


def _to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _extract_age_months(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str).str.extract(r"([0-9]+(?:\.[0-9]+)?)")[0],
        errors="coerce",
    )


def _normalize_sd_vp(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip().str.upper()
    s = s.replace({
        "VP ": "VP",
        " SD": "SD",
        "V P": "VP",
        "S D": "SD",
    })
    return s


def _drop_empty_unnamed_columns(df: pd.DataFrame) -> pd.DataFrame:
    keep_cols = []
    for col in df.columns:
        col_text = str(col).strip()
        if col_text == "":
            continue
        if col_text.lower().startswith("unnamed:"):
            continue
        keep_cols.append(col)
    return df[keep_cols]


def _clean_raw_dataframe(raw: pd.DataFrame) -> pd.DataFrame:
    raw = raw.copy()
    raw = _drop_empty_unnamed_columns(raw)
    raw = raw.dropna(how="all")
    raw.columns = [_clean_text(c) for c in raw.columns]
    return raw.reset_index(drop=True)


def _try_read_sheet(file_bytes: bytes, sheet_name: str, header: int = 0) -> pd.DataFrame:
    df = pd.read_excel(BytesIO(file_bytes), sheet_name=sheet_name, header=header)
    return _clean_raw_dataframe(df)


def _read_best_sheet(file_bytes: bytes) -> pd.DataFrame:
    excel = pd.ExcelFile(BytesIO(file_bytes))
    sheet_name = _pick_best_sheet(excel, file_bytes)

    raw0 = _try_read_sheet(file_bytes, sheet_name, header=0)
    score0 = _score_sheet(raw0)

    try:
        raw1 = _try_read_sheet(file_bytes, sheet_name, header=1)
        score1 = _score_sheet(raw1)
    except Exception:
        raw1 = None
        score1 = -1

    if raw1 is not None and score1 > score0:
        return raw1

    return raw0


def load_and_normalize_excel(file_bytes: bytes) -> pd.DataFrame:
    raw = _read_best_sheet(file_bytes)

    mapped: dict[str, pd.Series] = {}

    for target_name, aliases in COLUMN_ALIASES.items():
        source_col = _find_column(raw, aliases)
        if source_col is not None:
            mapped[target_name] = raw[source_col]

    df = pd.DataFrame(mapped)

    for col in ["estate", "division", "field_no"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    if "sd_vp" in df.columns:
        df["sd_vp"] = _normalize_sd_vp(df["sd_vp"])

    if "age_months" in df.columns:
        df["age_months"] = _extract_age_months(df["age_months"])

    for col in ["bc", "hect", "crop", "yph"]:
        if col in df.columns:
            df[col] = _to_numeric(df[col])

    df = df.dropna(how="all").reset_index(drop=True)
    return df