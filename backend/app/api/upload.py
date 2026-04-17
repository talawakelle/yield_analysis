from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from typing import List

from app.core.config import settings
from app.services.auth_service import require_admin
from app.services.data_store import (
    save_dashboard_dataset,
    save_region_frames,
    save_upload_metadata,
    set_active_dataset,
)
from app.services.dashboard_service import build_dashboard_dataset
from app.services.normalization_service import load_and_normalize_excel
from app.services.validation_service import (
    validate_normalized_columns,
    validate_region_rules,
)
from app.services.month_detection_service import detect_month_from_filename
from app.services.mapping_service import load_region_code_map, attach_codes
from app.services.calculation_service import run_report_pipeline

router = APIRouter()
TEMP_UPLOADS: dict[str, dict] = {}


def _canonical_region(region: str) -> str:
    value = "" if region is None else str(region).strip().upper()
    if value == "LC":
        return "TTEL_LC"
    if value == "RB":
        return "HT"
    return value


@router.post("/monthly-datasets")
async def upload_monthly_datasets(
    files: List[UploadFile] = File(...),
    _session=Depends(require_admin),
) -> dict:
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    mapping_file = settings.resolved_mapping_file

    loaded = {}
    master_maps = {}
    validation = {}
    detected_months = set()

    for file in files:
        try:
            content = await file.read()

            detected_month = detect_month_from_filename(file.filename)
            if not detected_month:
                raise HTTPException(
                    status_code=400,
                    detail=f"Could not detect month/year from file name: {file.filename}",
                )

            detected_months.add(detected_month)
            region_key = _canonical_region(file.filename.split()[0].upper())

            df = load_and_normalize_excel(content)

            missing_columns = validate_normalized_columns(list(df.columns))
            region_issues = validate_region_rules(region_key, list(df.columns))

            validation[region_key] = {
                "missing_columns": missing_columns,
                "region_issues": region_issues,
                "row_count": int(len(df)),
                "columns": list(df.columns),
                "detected_month": detected_month,
                "filename": file.filename,
            }

            if missing_columns:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "message": f"Missing required columns in {file.filename}",
                        "region": region_key,
                        "missing_columns": missing_columns,
                    },
                )

            if region_issues:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "message": f"Region-specific validation failed in {file.filename}",
                        "region": region_key,
                        "issues": region_issues,
                    },
                )

            if mapping_file.exists():
                mapping_df = load_region_code_map(str(mapping_file), region_key)
                master_maps[region_key] = mapping_df.copy()
                df = attach_codes(df, mapping_df)

                validation[region_key]["mapping_file_used"] = str(mapping_file)
                validation[region_key]["mapping_rows"] = int(len(mapping_df))
                validation[region_key]["mapped_code_count"] = int(df["code"].notna().sum()) if "code" in df.columns else 0
            else:
                df["code"] = df["division"].astype(str).str[:2].str.upper()
                validation[region_key]["mapping_file_used"] = None
                validation[region_key]["mapping_rows"] = 0
                validation[region_key]["mapped_code_count"] = int(df["code"].notna().sum())
                validation[region_key]["mapping_warning"] = f"Mapping workbook not found: {mapping_file}. Fallback code used."

            loaded[region_key] = df

        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": f"Failed to read or normalize file: {file.filename}",
                    "region": _canonical_region(file.filename.split()[0].upper()) if file.filename else "UNKNOWN",
                    "error": str(exc),
                },
            )

    if len(detected_months) != 1:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Uploaded files do not belong to the same month.",
                "detected_months": sorted(detected_months),
            },
        )

    selected_month = detected_months.pop()
    TEMP_UPLOADS[selected_month] = {
        "frames": loaded,
        "master_maps": master_maps,
        "validation": validation,
    }

    calc = run_report_pipeline(loaded, selected_month, master_maps={})
    dashboard_df = build_dashboard_dataset(calc, selected_month)

    save_region_frames(selected_month, loaded)
    save_dashboard_dataset(selected_month, dashboard_df)
    set_active_dataset(selected_month)

    dashboard_stats = {
        "row_count": int(len(dashboard_df)),
        "region_count": int(dashboard_df["region"].nunique()) if not dashboard_df.empty else 0,
        "estate_count": int(dashboard_df["estate"].nunique()) if not dashboard_df.empty else 0,
        "division_count": int(dashboard_df["division"].nunique()) if not dashboard_df.empty else 0,
        "year_count": int(dashboard_df["year"].nunique()) if not dashboard_df.empty else 0,
    }

    save_upload_metadata(
        selected_month,
        {
            "selected_month": selected_month,
            "regions": sorted(loaded.keys()),
            "validation": validation,
            "dashboard_stats": dashboard_stats,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    return {
        "message": "Files uploaded, normalized, validated, mapped, and activated successfully.",
        "selected_month": selected_month,
        "regions": sorted(loaded.keys()),
        "validation": validation,
        "dashboard_stats": dashboard_stats,
    }
