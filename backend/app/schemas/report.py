from pydantic import BaseModel


class GenerateReportRequest(BaseModel):
    selected_month: str | None = None
    output_mode: str = "region"
