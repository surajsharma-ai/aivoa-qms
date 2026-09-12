from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AIVOA QMS Complaint Copilot"
    groq_api_key: str = ""
    groq_model: str = "gemma2-9b-it"
    groq_context_model: str = "openai/gpt-oss-120b"
    database_url: str = "sqlite:///./aivoa_qms.db"
    cors_origins: str = "*"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
