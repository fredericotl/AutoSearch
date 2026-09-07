from pydantic import EmailStr, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from sqlalchemy.engine import make_url

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    sender_email: EmailStr
    sender_password: str = Field(min_length=16, max_length=16)
    secret_key: str
    sqlalchemy_database_url: str
    log_level: str = Field(default="INFO")
    time_zone: str = Field(default="America/Sao_Paulo")
    window_of_days: int = 365

    @field_validator("sqlalchemy_database_url")
    @classmethod
    def _anchor_sqlite(cls, value: str) -> str:
        url = make_url(value)
        if url.get_backend_name() != "sqlite" or not url.database:
            return value

        path = Path(url.database)
        if path.is_absolute():
            return value

        anchored = (BASE_DIR / path).resolve()
        return url.set(database=anchored.as_posix()).render_as_string(hide_password=False)

settings = Settings()



