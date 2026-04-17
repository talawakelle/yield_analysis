def validate_normalized_columns(columns: list[str]) -> list[str]:
    from app.core.constants import REQUIRED_NORMALIZED_COLUMNS

    return [col for col in REQUIRED_NORMALIZED_COLUMNS if col not in columns]


def validate_region_rules(region_name: str, columns: list[str]) -> list[str]:
    issues: list[str] = []
    region_key = str(region_name).strip().upper()

    if region_key in {"LC", "TTEL_LC", "KVPL_LC", "HPL_LC"} and "bc" not in columns:
        issues.append(f"{region_key} upload must include BC column.")

    return issues