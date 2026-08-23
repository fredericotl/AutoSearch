from pydantic import EmailStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    sender_email: EmailStr
    sender_password: str = Field(min_length=16, max_length=16)
    secret_key: str
    sqlalchemy_database_url: str

settings = Settings()



