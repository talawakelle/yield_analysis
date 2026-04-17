DISPLAY_SHEETS = [
    "1st YEAR VP YIELD",
    "2nd YEAR VP YIELD",
    "3rd YEAR VP YIELD",
    "4th YEAR VP YIELD",
    "5th YEAR VP YIELD",
    "VP YIELD",
    "SD YIELD",
    "TOTAL (VP + SD) YIELD",
    "ABSTRACT SUMMARY",
]

AGE_GROUPS = {
    "1st YEAR VP YIELD": (1, 12),
    "2nd YEAR VP YIELD": (13, 24),
    "3rd YEAR VP YIELD": (25, 36),
    "4th YEAR VP YIELD": (37, 48),
    "5th YEAR VP YIELD": (49, 9999),
}

REQUIRED_NORMALIZED_COLUMNS = [
    "estate",
    "division",
    "field_no",
    "age_months",
    "sd_vp",
    "hect",
    "crop",
    "yph",
]

OPTIONAL_COLUMNS = ["bc"]