from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongodb_uri: str
    database_name: str = "document_analyzer"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()

ALLOWED_EXTENSIONS = [".pdf",".txt"]

MAX_FILE_SIZE = 10

UPLOAD_DIR = "uploads"