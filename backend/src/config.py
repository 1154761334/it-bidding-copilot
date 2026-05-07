from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://bidding_user:bidding_password@localhost:5433/bidding_db"

    # Optional MinIO compatibility settings. Not required for the current /bid flow.
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = ""
    MINIO_SECRET_KEY: str = ""
    MINIO_SECURE: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # LLM - OpenAI-compatible provider.
    LLM_BASE_URL: str = "https://ark.cn-beijing.volces.com/api/coding/v3"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "kimi-k2.6"

    # Embeddings - OpenAI-compatible provider.
    EMBEDDING_BASE_URL: str = "https://api.siliconflow.cn/v1"
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_MODEL: str = "Pro/BAAI/bge-m3"
    EMBEDDING_DIM: int = 1024

    # Local project/artifact workspace. This is ignored by git.
    BIDDING_DATA_DIR: str = "/root/it-bidding-copilot/workspaces/api-projects"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
