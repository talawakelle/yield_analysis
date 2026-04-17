from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import shutil

from app.core.paths import OUTPUTS_DIR, create_run_dir, ensure_dir
from app.core.template_config import canonical_region, get_region_template


@dataclass
class RunContext:
    selected_month: str
    output_mode: str
    run_dir: Path

    @property
    def root_dir(self) -> Path:
        return self.run_dir

    def region_dir(self, region: str) -> Path:
        region_key = canonical_region(region)
        base = ensure_dir(self.run_dir / region_key)
        ensure_dir(base / "preview_png")
        ensure_dir(base / "preview_jpg")
        ensure_dir(base / "preview_svg")
        ensure_dir(base / "VP")
        ensure_dir(base / "pages")
        return base


def create_run_context(selected_month: str, output_mode: str = "region") -> RunContext:
    return RunContext(
        selected_month=selected_month,
        output_mode=output_mode,
        run_dir=create_run_dir(selected_month, output_mode),
    )


def path_to_output_url(path: str | Path) -> str:
    p = Path(path).resolve()
    try:
        rel = p.relative_to(OUTPUTS_DIR.resolve())
        return "/outputs/" + rel.as_posix()
    except Exception:
        return "/outputs/" + p.name


def copy_as_page_asset(source_image: str | Path, region_dir: str | Path, page_name: str) -> dict[str, str]:
    source = Path(source_image)
    region_path = ensure_dir(region_dir)
    pages_dir = ensure_dir(region_path / "pages")
    target = pages_dir / page_name

    if not source.exists() and source.suffix.lower() == ".png":
        alt = source.parent.parent / "preview_jpg" / f"{source.stem}.jpg"
        if alt.exists():
            source = alt

    if not source.exists() and source.suffix.lower() == ".jpg":
        alt = source.parent.parent / "preview_png" / f"{source.stem}.png"
        if alt.exists():
            source = alt

    if not source.exists():
        raise FileNotFoundError(f"Page asset source not found: {source}")

    shutil.copyfile(source, target)
    return {"path": str(target), "url": path_to_output_url(target)}


def save_manifest(ctx: RunContext, manifest: dict) -> Path:
    manifest_path = ctx.root_dir / "report_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    return manifest_path


def build_region_manifest(region: str, assets: list[dict]) -> dict:
    tpl = get_region_template(region)
    return {
        "region": canonical_region(region),
        "template_id": tpl.template_id,
        "company": tpl.company,
        "assets": assets,
    }
