import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Browser Agent API"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./browser_agent.db")
    MAX_AGENT_STEPS: int = int(os.getenv("MAX_AGENT_STEPS", "30"))
    HEADLESS: bool = os.getenv("HEADLESS", "false").lower() == "true"
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
