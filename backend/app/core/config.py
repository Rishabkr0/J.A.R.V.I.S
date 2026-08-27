from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = 'JARVIS'
    ENVIRONMENT: str = 'development'
    HOST: str = '0.0.0.0'
    PORT: int = 8000
    LOG_LEVEL: str = 'INFO'
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = 'gemini-2.5-flash'
    MAX_CONVERSATION_MESSAGES: int = 20

    class Config:
        env_file = '.env'

settings = Settings()
