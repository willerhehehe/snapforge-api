from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_key: str = ""
    rate_limit_per_minute: int = 60
    max_image_size_mb: int = 10
    port: int = 8080
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    paddle_api_key: str = ""
    paddle_webhook_secret: str = ""
    paddle_client_token: str = ""
    paddle_environment: str = "sandbox"
    paddle_price_pro: str = ""
    paddle_price_business: str = ""
    base_url: str = ""
    session_secret: str = "snapforge-session-secret-change-me"
    smtp_user: str = ""
    smtp_password: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "env_prefix": "SNAPFORGE_"}


settings = Settings()
