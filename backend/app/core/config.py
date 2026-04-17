from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Plantation Yield Automation"
    app_public_title: str = "Plantation Yield Intelligence"
    app_public_subtitle: str = "Premium plantation analytics dashboard"
    admin_username: str = "datainput"
    admin_password: str = "data123"
    admin_token_expiry_hours: int = 24
    access_file_path: str = str(BASE_DIR / "data" / "user_estate_access.json")
    access_strict_mode: bool = True

    temp_dir: str = "./temp"
    output_dir: str = "./outputs"
    data_store_dir: str = "./data_store"

    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    )

    mapping_file_path: str = ""

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors_origins(cls, value):
        if value is None or value == "":
            return [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
            ]
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def resolved_mapping_file(self) -> Path:
        if self.mapping_file_path:
            return Path(self.mapping_file_path)
        return BASE_DIR / "data" / "Estate Divisional Codes TTEL KVPL HPL.xlsx"


settings = Settings()
