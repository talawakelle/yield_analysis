from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from app.api.upload import TEMP_UPLOADS
from app.schemas.report import GenerateReportRequest
from app.services.abstract_service import render_abstract_summary
from app.services.auth_service import require_admin
from app.services.calculation_service import run_report_pipeline
from app.services.chart_service import render_chart
from app.services.data_store import get_active_dataset, load_region_frames, set_active_report
from app.services.export_service import (
    export_excel,
    export_pdf_from_images,
    export_zip_package,
)
from app.services.render_service import (
    build_region_manifest,
    copy_as_page_asset,
    create_run_context,
    path_to_output_url,
    save_manifest,
)

router = APIRouter()


@router.post("/generate")
def generate(payload: GenerateReportRequest, _session=Depends(require_admin)) -> dict:
    selected_month = payload.selected_month or get_active_dataset()
    if not selected_month:
        raise HTTPException(status_code=404, detail="No uploaded dataset found.")

    staged = TEMP_UPLOADS.get(selected_month)
    if staged:
        frames = staged["frames"]
    else:
        frames = load_region_frames(selected_month)

    if not frames:
        raise HTTPException(status_code=404, detail="No uploaded temp files found for selected month.")

    calc = run_report_pipeline(
        frames,
        selected_month,
        master_maps={},
    )

    ctx = create_run_context(selected_month, payload.output_mode)

    preview_images: list[str] = []
    preview_images_png: list[str] = []
    preview_images_svg: list[str] = []
    pdf_image_paths: list[str] = []
    region_manifests: list[dict] = []

    for region, sheets in calc.outputs.items():
        region_dir = ctx.region_dir(region)
        region_assets: list[dict] = []
        region_pdf_images: list[str] = []

        for title, df in sheets.items():
            if title == "ABSTRACT SUMMARY":
                png_path = render_abstract_summary(df, region, str(region_dir))
                summary_name = Path(png_path).stem
                jpg_path = str(Path(region_dir) / "preview_jpg" / f"{summary_name}.jpg")
                svg_path = str(Path(region_dir) / "preview_svg" / f"{summary_name}.svg")

                page = copy_as_page_asset(png_path, region_dir, "abstract_summary.png")
                asset = {
                    "title": title,
                    "kind": "abstract_summary",
                    "png": path_to_output_url(png_path),
                    "jpg": path_to_output_url(jpg_path),
                    "svg": path_to_output_url(svg_path),
                    "page_png": page["url"],
                }
                preview_images.append(asset["jpg"])
                preview_images_png.append(asset["png"])
                preview_images_svg.append(asset["svg"])
                pdf_image_paths.append(png_path)
                region_pdf_images.append(png_path)
                region_assets.append(asset)
                continue

            if hasattr(df, "empty"):
                jpg_path = render_chart(
                    df, region, title, selected_month, str(region_dir)
                )

                graph_name = Path(jpg_path).stem
                png_path = str(Path(region_dir) / "preview_png" / f"{graph_name}.png")
                svg_path = str(Path(region_dir) / "preview_svg" / f"{graph_name}.svg")

                page = copy_as_page_asset(png_path, region_dir, f"{graph_name}.png")
                asset = {
                    "title": title,
                    "kind": "chart",
                    "png": path_to_output_url(png_path),
                    "jpg": path_to_output_url(jpg_path),
                    "svg": path_to_output_url(svg_path),
                    "page_png": page["url"],
                }
                preview_images.append(asset["jpg"])
                preview_images_png.append(asset["png"])
                preview_images_svg.append(asset["svg"])
                pdf_image_paths.append(png_path)
                region_pdf_images.append(png_path)
                region_assets.append(asset)

        region_pdf_path = export_pdf_from_images(
            region_pdf_images,
            str(region_dir),
            f"{Path(str(region)).stem.lower()}_report.pdf",
        )
        region_manifest = build_region_manifest(region, region_assets)
        region_manifest["downloads"] = {
            "pdf": path_to_output_url(region_pdf_path),
        }
        region_manifests.append(region_manifest)

    excel_path = export_excel(calc.outputs, str(ctx.root_dir))
    pdf_path = export_pdf_from_images(pdf_image_paths, str(ctx.root_dir), "report.pdf")
    zip_path = export_zip_package(str(ctx.root_dir), "report_package.zip")

    manifest = {
        "selected_month": selected_month,
        "output_mode": payload.output_mode,
        "run_dir": path_to_output_url(ctx.root_dir),
        "regions": [r["region"] for r in region_manifests],
        "region_outputs": region_manifests,
        "downloads": {
            "excel": path_to_output_url(excel_path),
            "pdf": path_to_output_url(pdf_path),
            "zip": path_to_output_url(zip_path),
        },
        "preview_images": preview_images,
        "preview_images_png": preview_images_png,
        "preview_images_svg": preview_images_svg,
    }
    manifest_path = save_manifest(ctx, manifest)
    manifest["manifest"] = path_to_output_url(manifest_path)
    set_active_report(manifest)

    return {
        "message": "Actual report generation completed.",
        "selected_month": selected_month,
        "output_mode": payload.output_mode,
        "run_dir": path_to_output_url(ctx.root_dir),
        "regions": [r["region"] for r in region_manifests],
        "downloads": manifest["downloads"],
        "preview_images": preview_images,
        "preview_images_png": preview_images_png,
        "preview_images_svg": preview_images_svg,
        "manifest": manifest["manifest"],
        "region_outputs": region_manifests,
    }
