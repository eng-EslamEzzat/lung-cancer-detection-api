"""
Core configuration settings for the FastAPI Lung Cancer Detection service
"""

from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import field_validator
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "Lung Cancer Detection API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "FastAPI microservice for lung cancer detection from medical images"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # CORS (simplified for local testing)
    ALLOWED_ORIGINS: str = "*"  # Will be processed in main.py
    ALLOWED_METHODS: List[str] = ["GET", "POST"]
    ALLOWED_HEADERS: List[str] = ["*"]
    
    # File Upload
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_IMAGE_TYPES: str = "image/jpeg,image/png,image/tiff,image/bmp"  # Will be parsed
    
    # Model Settings (Docker and local compatible)
    MODEL_PATH: str = "./models/lung_cancer_model.h5"
    MODEL_INPUT_SIZE: str = "224,224"  # Default input size as string
    CONFIDENCE_THRESHOLD: float = 0.5
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    
    # Health Check
    HEALTH_CHECK_INTERVAL: int = 30
    
    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value):
        if isinstance(value, str):
            return value.lower() in ("true", "1", "on", "yes")
        return value
    
    def get_model_input_size(self) -> tuple:
        """Parse model input size from string to tuple"""
        try:
            width, height = self.MODEL_INPUT_SIZE.split(",")
            return (int(width.strip()), int(height.strip()))
        except:
            return (224, 224)  # default
    
    def get_allowed_origins(self) -> List[str]:
        """Parse allowed origins from string to list"""
        if self.ALLOWED_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    def get_allowed_image_types(self) -> List[str]:
        """Parse allowed image types from string to list"""
        return [img_type.strip() for img_type in self.ALLOWED_IMAGE_TYPES.split(",")]
    
    def get_model_path(self) -> str:
        """Get absolute model path that works in both local and Docker environments"""
        import os
        if os.path.isabs(self.MODEL_PATH):
            return self.MODEL_PATH
        # Convert relative path to absolute, works in both environments
        return os.path.abspath(self.MODEL_PATH)
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()