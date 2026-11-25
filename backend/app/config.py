from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    aws_region: str = "ap-south-1"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None

    s3_bucket: str = "clueberry-documents"
    dynamodb_table: str = "ClueBerryEvidence"

    bedrock_model_id: str = "anthropic.claude-sonnet-4-5"
    textract_enabled: bool = False

    elevenlabs_api_key: Optional[str] = None
    elevenlabs_enabled: bool = False

    max_upload_size_mb: int = 10
    cors_origins: str = "http://localhost:5173"

    class Config:
        env_file = ".env"

settings = Settings()
