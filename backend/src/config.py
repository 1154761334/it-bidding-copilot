from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VAULT_ROOT = _REPO_ROOT / "vault"
DEFAULT_DEMO_TENDER_PATH = DEFAULT_VAULT_ROOT / "10-Knowledge/Evergreen/招标文件案例.md"
DEFAULT_BIDDING_DATA_DIR = _REPO_ROOT / "workspaces/api-projects"


def repo_path(value: str | Path) -> Path:
    """Resolve configured project paths relative to the repository root."""
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return _REPO_ROOT / path


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

    # Local repository paths. These directories are ignored by git when they
    # contain generated project state or private source materials.
    REPO_ROOT: str = str(_REPO_ROOT)
    VAULT_ROOT: str = str(DEFAULT_VAULT_ROOT)
    DEMO_TENDER_PATH: str = str(DEFAULT_DEMO_TENDER_PATH)
    BIDDING_DATA_DIR: str = str(DEFAULT_BIDDING_DATA_DIR)

    model_config = SettingsConfigDict(
        env_file=(str(_REPO_ROOT / ".env"), str(_REPO_ROOT / "backend/.env")),
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()
