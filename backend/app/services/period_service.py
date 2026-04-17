from datetime import datetime


def april_start_for_selected_month(selected_month: str) -> str:
    # selected_month format: YYYY-MM
    dt = datetime.strptime(selected_month, "%Y-%m")
    start_year = dt.year if dt.month >= 4 else dt.year - 1
    return f"{start_year}-04"


def month_range_label(selected_month: str) -> str:
    start = april_start_for_selected_month(selected_month)
    return f"{start} to {selected_month}"