
from __future__ import annotations

from dataclasses import dataclass

REGION_ALIASES = {
    "LC": "TTEL_LC",
    "RB": "HT",
}

LEGACY_GRAPH_NAMES = {
    "1st YEAR VP YIELD": "Graph 1",
    "2nd YEAR VP YIELD": "Graph 2",
    "3rd YEAR VP YIELD": "Graph 3",
    "4th YEAR VP YIELD": "Graph 4",
    "5th YEAR VP YIELD": "Graph 5",
    "VP YIELD": "Graph VP",
    "SD YIELD": "Graph SD",
    "TOTAL (VP + SD) YIELD": "Graph Tot",
    "ABSTRACT SUMMARY": "Abstract Summary",
}


@dataclass(frozen=True)
class RegionTemplate:
    template_id: str
    company: str
    page_size: str = "A3-landscape"
    chart_dpi: int = 320
    export_png_dpi: int = 320
    export_jpg_quality: int = 100
    font_family: str = "serif"
    include_inset_variant: bool = False


REGION_TEMPLATES: dict[str, RegionTemplate] = {
    "TK": RegionTemplate("TTEL_TK", "TTEL", include_inset_variant=True),
    "NO": RegionTemplate("TTEL_NO", "TTEL"),
    "TTEL_LC": RegionTemplate("TTEL_LC", "TTEL"),
    "NE": RegionTemplate("KVPL_NE", "KVPL", include_inset_variant=True),
    "HT": RegionTemplate("KVPL_HT", "KVPL", include_inset_variant=True),
    "KVPL_LC": RegionTemplate("KVPL_LC", "KVPL"),
    "UC": RegionTemplate("HPL_UC", "HPL"),
    "LD": RegionTemplate("HPL_LD", "HPL"),
    "HPL_LC": RegionTemplate("HPL_LC", "HPL"),
}


def canonical_region(region: str) -> str:
    value = "" if region is None else str(region).strip().upper()
    return REGION_ALIASES.get(value, value)


def get_region_template(region: str) -> RegionTemplate:
    return REGION_TEMPLATES.get(canonical_region(region), RegionTemplate("DEFAULT", "TTEL"))
