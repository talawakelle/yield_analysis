
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from app.services.access_service import apply_access_scope, resolve_access_context, serialize_access_context
from app.services.dashboard_service import (
    export_rows_csv,
    get_active_dataset_df,
    get_chart_data,
    get_dashboard_status,
    get_estate_summary,
    get_filter_options,
    get_region_summary,
    parse_dashboard_question,
    run_dashboard_query,
)

router = APIRouter()


def _require_dataset(request: Request):
    selected_month, df = get_active_dataset_df()
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="No active dataset found. Upload monthly files from the admin page first.")

    access = resolve_access_context(request, df)
    if access.access_mode == "restricted":
        raise HTTPException(status_code=401, detail=access.access_message or "Open this project through the central login portal.")

    scoped_df = apply_access_scope(df, access)
    if scoped_df is None or scoped_df.empty:
        raise HTTPException(status_code=403, detail="This account does not have access to any plantation data in the active dataset.")

    return selected_month, scoped_df, access


@router.get("/status")
def status(request: Request) -> dict:
    selected_month, df = get_active_dataset_df()
    access = resolve_access_context(request, df)
    if df is not None and not df.empty and access.access_mode != "restricted":
        df = apply_access_scope(df, access)
    return {
        **get_dashboard_status(df_override=df, selected_month_override=selected_month),
        "access": serialize_access_context(access),
    }


@router.get("/options")
def options(request: Request) -> dict:
    selected_month, df, access = _require_dataset(request)
    return {
        "selected_month": selected_month,
        "options": get_filter_options(df),
        "access": serialize_access_context(access),
    }


@router.get("/query")
def query(
    request: Request,
    plantation: str = "",
    region: str = "",
    estate: str = "",
    division: str = "",
    year: str = "",
    metric: str = "Division_Yield",
    operator: str = "",
    value: float | None = Query(default=None),
    rank_dir: str = "",
    count: int = 10,
    benchmark_metric: str = "",
) -> dict:
    selected_month, df, access = _require_dataset(request)
    result = run_dashboard_query(
        df,
        plantation=plantation,
        region=region,
        estate=estate,
        division=division,
        year=year,
        metric=metric,
        operator=operator,
        value=value,
        rank_dir=rank_dir,
        count=count,
        benchmark_metric=benchmark_metric,
    )
    result["selected_month"] = selected_month
    result["access"] = serialize_access_context(access)
    return result


@router.get("/ask")
def ask(request: Request, question: str) -> dict:
    selected_month, df, access = _require_dataset(request)
    inferred = parse_dashboard_question(df, question)
    result = run_dashboard_query(df, **inferred)
    result["selected_month"] = selected_month
    result["question"] = question
    result["inferred"] = inferred
    result["access"] = serialize_access_context(access)
    return result


@router.get("/region-summary")
def region_summary(request: Request, region: str, year: str) -> dict:
    _, df, _ = _require_dataset(request)
    result = get_region_summary(df, region=region, year=year)
    if not result:
        raise HTTPException(status_code=404, detail="No region summary found.")
    return result


@router.get("/estate-summary")
def estate_summary(
    request: Request,
    plantation: str,
    estate: str,
    year: str,
    division: str = "",
) -> dict:
    _, df, _ = _require_dataset(request)
    result = get_estate_summary(df, plantation=plantation, estate=estate, year=year, division=division)
    if not result:
        raise HTTPException(status_code=404, detail="No estate summary found.")
    return result


@router.get("/chart")
def chart(
    request: Request,
    region: str,
    year: str,
    metric: str = "Division_Yield",
    focus_estate: str = "",
    focus_division: str = "",
) -> dict:
    _, df, _ = _require_dataset(request)
    return get_chart_data(
        df,
        region=region,
        year=year,
        metric=metric,
        focus_estate=focus_estate,
        focus_division=focus_division,
    )


@router.get("/export.csv", response_class=PlainTextResponse)
def export_csv(
    request: Request,
    plantation: str = "",
    region: str = "",
    estate: str = "",
    division: str = "",
    year: str = "",
    metric: str = "Division_Yield",
    operator: str = "",
    value: float | None = Query(default=None),
    rank_dir: str = "",
    count: int = 10,
    benchmark_metric: str = "",
) -> PlainTextResponse:
    _, df, _ = _require_dataset(request)
    result = run_dashboard_query(
        df,
        plantation=plantation,
        region=region,
        estate=estate,
        division=division,
        year=year,
        metric=metric,
        operator=operator,
        value=value,
        rank_dir=rank_dir,
        count=count,
        benchmark_metric=benchmark_metric,
    )
    content = export_rows_csv(result["rows"])
    return PlainTextResponse(content=content, media_type="text/csv")
