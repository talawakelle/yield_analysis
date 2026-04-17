from __future__ import annotations

from pathlib import Path
import json
import pandas as pd

from app.core.paths import DATA_STORE_DIR, ensure_dir


ACTIVE_DATASET_FILE = DATA_STORE_DIR / "active_dataset.json"
ACTIVE_REPORT_FILE = DATA_STORE_DIR / "active_report.json"


def month_dir(selected_month: str) -> Path:
    return ensure_dir(DATA_STORE_DIR / "datasets" / selected_month)


def normalized_dir(selected_month: str) -> Path:
    return ensure_dir(month_dir(selected_month) / "normalized")


def dashboard_dataset_path(selected_month: str) -> Path:
    return month_dir(selected_month) / "dashboard_dataset.csv"


def upload_meta_path(selected_month: str) -> Path:
    return month_dir(selected_month) / "upload_meta.json"


def save_region_frames(selected_month: str, region_frames: dict[str, pd.DataFrame]) -> list[str]:
    saved: list[str] = []
    out_dir = normalized_dir(selected_month)
    for region, df in region_frames.items():
        path = out_dir / f"{region}.csv"
        df.to_csv(path, index=False)
        saved.append(str(path))
    return saved


def load_region_frames(selected_month: str) -> dict[str, pd.DataFrame]:
    out: dict[str, pd.DataFrame] = {}
    src_dir = normalized_dir(selected_month)
    if not src_dir.exists():
        return out
    for path in sorted(src_dir.glob("*.csv")):
        out[path.stem] = pd.read_csv(path)
    return out


def save_dashboard_dataset(selected_month: str, df: pd.DataFrame) -> str:
    path = dashboard_dataset_path(selected_month)
    df.to_csv(path, index=False)
    return str(path)


def load_dashboard_dataset(selected_month: str) -> pd.DataFrame | None:
    path = dashboard_dataset_path(selected_month)
    if not path.exists():
        return None
    return pd.read_csv(path)


def save_upload_metadata(selected_month: str, payload: dict) -> str:
    path = upload_meta_path(selected_month)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(path)


def load_upload_metadata(selected_month: str) -> dict | None:
    path = upload_meta_path(selected_month)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def list_uploaded_months() -> list[dict]:
    root = DATA_STORE_DIR / "datasets"
    if not root.exists():
        return []
    items = []
    for month_path in sorted(root.iterdir(), reverse=True):
        if not month_path.is_dir():
            continue
        meta = load_upload_metadata(month_path.name) or {}
        items.append(
            {
                "selected_month": month_path.name,
                "available_regions": meta.get("regions", []),
                "uploaded_at": meta.get("uploaded_at"),
                "row_count": meta.get("dashboard_stats", {}).get("row_count", 0),
            }
        )
    return items


def set_active_dataset(selected_month: str) -> None:
    ACTIVE_DATASET_FILE.write_text(
        json.dumps({"selected_month": selected_month}, indent=2),
        encoding="utf-8",
    )


def get_active_dataset() -> str | None:
    if not ACTIVE_DATASET_FILE.exists():
        return None
    return json.loads(ACTIVE_DATASET_FILE.read_text(encoding="utf-8")).get("selected_month")


def _normalize_active_report_payload(payload: dict | None) -> dict | None:
    if not payload:
        return payload

    normalized = dict(payload)

    region_outputs = normalized.get("region_outputs")
    regions = normalized.get("regions")

    # Older saved manifests stored full region manifest objects inside "regions".
    if not region_outputs and isinstance(regions, list) and regions and isinstance(regions[0], dict):
        region_outputs = regions

    if region_outputs and isinstance(region_outputs, list):
        normalized["region_outputs"] = region_outputs
        normalized["regions"] = [
            item.get("region", "") for item in region_outputs if isinstance(item, dict) and item.get("region")
        ]

    return normalized


def set_active_report(payload: dict) -> None:
    ACTIVE_REPORT_FILE.write_text(
        json.dumps(_normalize_active_report_payload(payload), indent=2),
        encoding="utf-8",
    )


def get_active_report() -> dict | None:
    if not ACTIVE_REPORT_FILE.exists():
        return None
    payload = json.loads(ACTIVE_REPORT_FILE.read_text(encoding="utf-8"))
    return _normalize_active_report_payload(payload)
