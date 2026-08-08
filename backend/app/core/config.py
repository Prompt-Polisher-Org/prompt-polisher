from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Prompt Polisher API"
    API_V1_STR: str = "/api/v1"

    # Database
    POSTGRES_USER: str = "user"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "prompt_db"

    # JWT / Security
    # IMPORTANT: Change this to a long random secret in production!
    # Generate one with: openssl rand -hex 32
    SECRET_KEY: str = "CHANGE_ME_to_a_long_random_secret_key_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30       # 30 minutes
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7          # 7 days

    # OAuth 2.0 — Google
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # OAuth 2.0 — GitHub
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""

    # Base URL for OAuth redirect callbacks (e.g. http://localhost:8000)
    OAUTH_REDIRECT_BASE_URL: str = "http://localhost:8000"

    # Redis Cache & Rate Limiting
    REDIS_HOST: str = "localhost"
    REDIS_PORT: str = "6379"
    REDIS_DB: str = "0"
    
    # AI Inference Server
    AI_INFERENCE_SERVER_URL: str = "http://localhost:8001"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

settings = Settings()