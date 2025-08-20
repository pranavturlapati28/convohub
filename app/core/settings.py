from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    TEST_DATABASE_URL: Optional[str] = None
    OPENAI_API_KEY: str
    JWT_SECRET: str = "dev"
    ENV: str = "dev"

    class Config:
        env_file = ".env"

settings = Settings()
