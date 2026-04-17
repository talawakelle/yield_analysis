from __future__ import annotations

from pathlib import Path
import re
import pandas as pd


MAPPING_SHEET = "Sheet1 (2)"

REGION_ALIASES = {
    "LC": "TTEL_LC",
    "RB": "HT",
}


REGION_SOURCES = {
    "TK": [("TTEL-TK", "DIVISION", "CODE")],
    "TTEL_LC": [("TTEL-LC", "DIVISION.1", "CODE.1")],
    "NE": [("KVPL-NE", "DIVISION.2", "CODE.2")],
    "HT": [("KVPL-NE", "DIVISION.2", "CODE.2")],
    "KVPL_LC": [("TTEL-LC", "DIVISION.1", "CODE.1")],
    "UC": [("HPL-UPCOT", "Division.1", "Code.1")],
    "LD": [("HPL-LD", "Division.2", "Code.2")],
    "HPL_LC": [
        ("HPL-UPCOT", "Division.1", "Code.1"),
        ("HPL-LD", "Division.2", "Code.2"),
    ],
}


REGION_INCLUDE_ESTATES = {
    "TK": {
        "BEARWELL",
        "HOLYROOD",
        "GREATWESTERN",
        "LOGIE",
        "MATTAKELLE",
        "PALMERSTON",
        "WATTEGODA",
    },
    "TTEL_LC": {"MORAGALLA", "KIRUWANAGANGA", "DENIYAYA", "INDOLA"},
    "NE": {"PEDRO", "NUWARAELIYA", "UDARADELLA", "GLASSUGH", "OLIPHANT", "EDINBURGH"},
    "HT": {"ANNFIELD", "BATTALGALLA", "INVERY", "INGESTRE", "FORDYCE", "ROBGILL", "TILLYRIE"},
    "KVPL_LC": {"KELANI", "KALUPAHANA", "HALGOLLA", "KITULGALA", "KITHULGALA"},
    "UC": {"ALTON", "FAIRLAWN", "GOURAVILLA", "MAHANILU", "STOCKHOLM"},
    "LD": {"BAMBARAKELLY", "EILDONHALL", "TILLICOULTRY"},
    "HPL_LC": {"MILLAKANDA"},
}


NO_MANUAL_MAPPING = [
    ("Dessford", "Dessford", "DF"),
    ("Dessford", "Lorne", "LN"),
    ("Dessford", "Lower", "DL"),
    ("Dessford", "Upper", "DU"),
    ("Radella", "RLower", "RL"),
    ("Radella", "RUpper", "RU"),
    ("Radella", "WLower", "WOL"),
    ("Radella", "WUpper", "WOU"),
    ("Calsay", "Calsay", "CA"),
    ("Calsay", "Maha Eliya", "ME"),
    ("Clarendon", "Avoca", "AV"),
    ("Clarendon", "Lower", "CL"),
    ("Clarendon", "Upper", "CU"),
    ("Somerset", "Carlabeck", "CB"),
    ("Somerset", "Dambagastalawa", "DT"),
    ("Somerset", "Easdale", "ED"),
    ("Somerset", "Langdale", "LA"),
    ("Somerset", "Somerset", "SS"),
]

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


def _canonical_region(region: str) -> str:
    value = "" if region is None else str(region).strip().upper()
    return REGION_ALIASES.get(value, value)


def _clean(v) -> str:
    if pd.isna(v):
        return ""
    text = str(v).strip()
    if text.lower() == "nan":
        return ""
    return text


def _norm(v) -> str:
    if pd.isna(v):
        return ""
    text = str(v).strip().upper()
    if text == "NAN":
        return ""
    return text


def _slug(v) -> str:
    return re.sub(r"[^A-Z0-9]+", "", _norm(v))


def _estate_key(v) -> str:
    return ESTATE_KEY_ALIASES.get(_slug(v), _slug(v))


def _division_key(v) -> str:
    return DIVISION_KEY_ALIASES.get(_slug(v), _slug(v))


def _canon_estate_name(v) -> str:
    text = _clean(v)
    key = _estate_key(text)

    if key == "GREATWESTERN":
        return "GreatWestern"
    if key == "NUWARAELIYA":
        return "Nuwaraeliya"
    if key == "UDARADELLA":
        return "Udaradella"
    if key == "STOCKHOLM":
        return "Stockholm"
    if key == "BAMBARAKELLY":
        return "Bambrakelly"
    return text


def _read_block(raw: pd.DataFrame, estate_col: str, division_col: str, code_col: str) -> pd.DataFrame:
    missing = [c for c in (estate_col, division_col, code_col) if c not in raw.columns]
    if missing:
        return pd.DataFrame(columns=["estate", "division", "code"])

    out = raw[[estate_col, division_col, code_col]].copy()
    out.columns = ["estate", "division", "code"]

    out["estate"] = out["estate"].ffill()
    out["estate"] = out["estate"].map(_canon_estate_name)
    out["division"] = out["division"].map(_clean)
    out["code"] = out["code"].map(_clean)

    out = out[(out["estate"] != "") & (out["division"] != "") & (out["code"] != "")].copy()

    bad_divisions = {"DIVISION", "ESTATE"}
    bad_codes = {"CODE"}
    out = out[
        ~out["division"].str.upper().isin(bad_divisions)
        & ~out["code"].str.upper().isin(bad_codes)
    ].copy()

    return out.reset_index(drop=True)


def _filter_region_estates(df: pd.DataFrame, region: str) -> pd.DataFrame:
    include = REGION_INCLUDE_ESTATES.get(region)
    if not include or df.empty:
        return df

    out = df.copy()
    out["_estate_key"] = out["estate"].map(_estate_key)
    out = out[out["_estate_key"].isin(include)].copy()
    return out.drop(columns=["_estate_key"]).reset_index(drop=True)


def load_region_code_map(mapping_file: str, region: str) -> pd.DataFrame:
    region = _canonical_region(region)

    if region == "NO":
        return pd.DataFrame(NO_MANUAL_MAPPING, columns=["estate", "division", "code"])

    path = Path(mapping_file)
    if not path.exists():
        raise FileNotFoundError(f"Mapping workbook not found: {mapping_file}")

    if region not in REGION_SOURCES:
        return pd.DataFrame(columns=["estate", "division", "code"])

    raw = pd.read_excel(path, sheet_name=MAPPING_SHEET)

    parts: list[pd.DataFrame] = []
    for estate_col, division_col, code_col in REGION_SOURCES[region]:
        block = _read_block(raw, estate_col, division_col, code_col)
        if block.empty:
            continue
        block = _filter_region_estates(block, region)
        if not block.empty:
            parts.append(block)

    if not parts:
        return pd.DataFrame(columns=["estate", "division", "code"])

    out = pd.concat(parts, ignore_index=True)
    out["estate"] = out["estate"].map(_canon_estate_name)
    out["division"] = out["division"].map(_clean)
    out["code"] = out["code"].map(_clean)

    out = out[(out["estate"] != "") & (out["division"] != "") & (out["code"] != "")]
    out = out.drop_duplicates(subset=["estate", "division"]).reset_index(drop=True)

    return out


def attach_codes(df: pd.DataFrame, mapping_df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    if "estate" not in out.columns or "division" not in out.columns:
        raise KeyError("attach_codes() requires 'estate' and 'division' columns in df")

    out["estate"] = out["estate"].map(_canon_estate_name)
    out["division"] = out["division"].astype(str).str.strip()

    if mapping_df.empty:
        out["code"] = out["division"].astype(str).str[:2].str.upper()
        return out

    mapping_df = mapping_df.copy()
    mapping_df["estate"] = mapping_df["estate"].map(_canon_estate_name)
    mapping_df["division"] = mapping_df["division"].astype(str).str.strip()
    mapping_df["code"] = mapping_df["code"].astype(str).str.strip()

    out["_estate_key"] = out["estate"].map(_estate_key)
    out["_division_key"] = out["division"].map(_division_key)
    mapping_df["_estate_key"] = mapping_df["estate"].map(_estate_key)
    mapping_df["_division_key"] = mapping_df["division"].map(_division_key)

    mapped = mapping_df[["_estate_key", "_division_key", "code"]].drop_duplicates(
        subset=["_estate_key", "_division_key"]
    )

    out = out.merge(mapped, on=["_estate_key", "_division_key"], how="left")
    out["code"] = out["code"].fillna(out["division"].astype(str).str[:2].str.upper())

    return out.drop(columns=["_estate_key", "_division_key"])


def load_region_master_map(mapping_file: str, region: str) -> pd.DataFrame:
    return load_region_code_map(mapping_file, region)
