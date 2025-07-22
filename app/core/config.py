from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # API Keys
    openai_api_key: str = ""
    zoopla_api_key: str = ""
    rightmove_api_key: str = ""
    google_maps_api_key: str = ""
    
    # Database
    database_url: str = "sqlite:///./reagent.db"
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Application
    environment: str = "development"
    log_level: str = "INFO"
    
    # Agent Configuration
    max_conversation_history: int = 50
    preference_learning_threshold: float = 0.7
    
    class Config:
        env_file = ".env"


def get_settings() -> Settings:
    return Settings() 