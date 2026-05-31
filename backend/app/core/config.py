from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    supabase_url: str
    supabase_service_key: str
    anthropic_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    nvidia_api_key: Optional[str] = None
    github_client_id: Optional[str] = None
    github_client_secret: Optional[str] = None
    github_webhook_secret: Optional[str] = None
    razorpay_key_id: str
    razorpay_key_secret: str
    postmark_api_key: Optional[str] = None
    from_email: str = "noreply@testura.dev"
    from_name: str = "Testura"
    redis_url: str = "redis://localhost:6379/0"
    repos_base_path: str = "C:/tmp/repos"
    allowed_origins: str = "http://localhost:3000"

    class Config:
        env_file = ".env"

settings = Settings()
