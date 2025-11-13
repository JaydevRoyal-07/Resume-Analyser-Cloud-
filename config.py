from pydantic import BaseSettings
import os

class Settings(BaseSettings):
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", 8000))
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://mongo:27017/resume_db")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "supersecret")
    ML_ANALYZER_URL: str = os.getenv("ML_ANALYZER_URL", "http://ml-analyzer:6000/analyze")

settings = Settings()
