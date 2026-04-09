from pathlib import Path
from typing import List, Dict
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    APP_NAME: str = "IT Bidding Copilot Industrial API"
    APP_VERSION: str = "2.0.0"
    APP_ENV: str = "development"
    DATABASE_URL: str = "postgresql://root:bidcore_password123@localhost:5432/bidcore_enterprise"

    # --- Path Configuration ---
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent
    DATA_DIR: Path = PROJECT_ROOT / "data"
    VECTOR_STORE_DIR: Path = DATA_DIR / "knowledge_base"
    ENTERPRISE_DIR: Path = DATA_DIR / "enterprises"
    ASSETS_DIR: Path = DATA_DIR / "assets"
    ASSET_IMAGES_DIR: Path = ASSETS_DIR / "images"
    ASSET_DOCS_DIR: Path = ASSETS_DIR / "docs"
    SESSIONS_DIR: Path = DATA_DIR / "sessions"
    TEMPLATES_DIR: Path = PROJECT_ROOT / "templates"

    # --- LLM & Embedding ---
    LLM_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    LLM_BASE_URL: str = ""
    OPENAI_BASE_URL: str = ""
    LLM_MODEL: str = "gpt-4o"
    MODEL_NAME: str = ""
    LLM_PROVIDER: str = "openai-compatible"
    EMBEDDING_MODEL: str = "BAAI/bge-m3"  # Default to BGE-M3 as decided

    # --- Component Configuration ---
    MINERU_API_URL: str = ""  # For remote MinerU processing
    LOCAL_EMBEDDING_PATH: str = "models/bge-m3-onnx"
    MAX_REVIEW_ROUNDS: int = 3

    # --- Business Domain Data ---
    WORKFLOW_STEPS: List[Dict] = [
        {"id": 1, "name": "企业档案管理", "icon": "🏢"},
        {"id": 2, "name": "RFP 拆解分析", "icon": "📋"},
        {"id": 3, "name": "协作编标", "icon": "✍️"},
        {"id": 4, "name": "人机交互大厅", "icon": "🤝"},
        {"id": 5, "name": "循环审标", "icon": "🔍"},
        {"id": 6, "name": "规范导出", "icon": "📦"},
    ]

    @property
    def resolved_llm_api_key(self) -> str:
        return self.LLM_API_KEY or self.OPENAI_API_KEY

    @property
    def resolved_llm_base_url(self) -> str:
        return self.LLM_BASE_URL or self.OPENAI_BASE_URL or "https://api.openai.com/v1"

    @property
    def resolved_llm_model(self) -> str:
        return self.LLM_MODEL or self.MODEL_NAME or "gpt-4o"

    def ensure_dirs(self):
        """Ensure all required data directories exist."""
        dirs = [
            self.DATA_DIR, self.VECTOR_STORE_DIR, self.ENTERPRISE_DIR, 
            self.ASSETS_DIR, self.ASSET_IMAGES_DIR, self.ASSET_DOCS_DIR, 
            self.SESSIONS_DIR
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)


def get_settings() -> Settings:
    s = Settings()
    s.ensure_dirs()
    return s


settings = get_settings()
