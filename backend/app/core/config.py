from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = 'JARVIS'
    ENVIRONMENT: str = 'development'
    HOST: str = '0.0.0.0'
    PORT: int = 8000
    LOG_LEVEL: str = 'INFO'
    
    # Provider Settings
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"
    
    # Voice Settings
    VOICE_ENABLED: bool = True
    WAKE_WORD_ENABLED: bool = True
    WAKEWORD_THRESHOLD: float = 0.25
    STT_MODEL: str = "base.en"
    STT_DEVICE: str = "cpu"
    STT_COMPUTE_TYPE: str = "int8"
    TTS_ENABLED: bool = True
    TTS_VOICE: str = "en_US-lessac-low"
    AUDIO_INPUT_DEVICE: int | None = None
    AUDIO_OUTPUT_DEVICE: int | None = None
    MAX_CONVERSATION_MESSAGES: int = 20

    class Config:
        env_file = '.env'

settings = Settings()
