from __future__ import annotations

from pathlib import Path
from datetime import datetime

from app.core.config import BASE_DIR, settings

OUTPUTS_DIR = (BASE_DIR / settings.output_dir).resolve()
TEMP_DIR = (BASE_DIR / settings.temp_dir).resolve()
DATA_STORE_DIR = (BASE_DIR / settings.data_store_dir).resolve()

for path in [OUTPUTS_DIR, TEMP_DIR, DATA_STORE_DIR]:
    path.mkdir(parents=True, exist_ok=True)

(OUTPUTS_DIR / "preview_png").mkdir(parents=True, exist_ok=True)
(OUTPUTS_DIR / "preview_jpg").mkdir(parents=True, exist_ok=True)
(OUTPUTS_DIR / "preview_svg").mkdir(parents=True, exist_ok=True)
(OUTPUTS_DIR / "VP").mkdir(parents=True, exist_ok=True)


def ensure_dir(path: Path | str) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def create_run_dir(selected_month: str, output_mode: str = "region") -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_month = selected_month.replace("/", "-")
    safe_mode = (output_mode or "region").strip().lower()
    run_dir = OUTPUTS_DIR / safe_month / f"{safe_mode}_{stamp}"
    ensure_dir(run_dir)
    return run_dir
