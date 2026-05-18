from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    supabase_url: str
    supabase_service_key: str
    anthropic_api_key: str
    github_client_id: str
    github_client_secret: str
    stripe_secret_key: str
    stripe_webhook_secret: str
    redis_url: str = "redis://localhost:6379/0"
    repos_base_path: str = "/tmp/repos"
    allowed_origins: str = "http://localhost:3000"

    class Config:
        env_file = ".env"

settings = Settings()
