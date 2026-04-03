"""
IT Bidding Copilot - 全局配置模块
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# 路径配置
# ============================================================
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = Path(os.getenv("APP_DATA_DIR", PROJECT_ROOT / "data"))
VECTOR_STORE_DIR = Path(os.getenv("VECTOR_STORE_DIR", DATA_DIR / "knowledge_base"))
ENTERPRISE_DIR = Path(os.getenv("ENTERPRISE_DIR", DATA_DIR / "enterprises"))
SESSIONS_DIR = DATA_DIR / "sessions"
TEMPLATES_DIR = PROJECT_ROOT / "templates"

# 确保数据目录存在
for d in [DATA_DIR, VECTOR_STORE_DIR, ENTERPRISE_DIR, SESSIONS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ============================================================
# LLM 配置
# ============================================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# ============================================================
# 应用常量
# ============================================================
MAX_REVIEW_ROUNDS = 3  # LangGraph 最大审标循环次数

# 业务步骤定义
WORKFLOW_STEPS = [
    {"id": 1, "name": "企业档案管理", "icon": "🏢"},
    {"id": 2, "name": "RFP 拆解分析", "icon": "📋"},
    {"id": 3, "name": "协作编标", "icon": "✍️"},
    {"id": 4, "name": "人机交互大厅", "icon": "🤝"},
    {"id": 5, "name": "循环审标", "icon": "🔍"},
    {"id": 6, "name": "规范导出", "icon": "📦"},
]


def get_llm():
    """获取配置好的 LangChain LLM 实例"""
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        openai_api_key=OPENAI_API_KEY,
        openai_api_base=OPENAI_BASE_URL,
        model_name=MODEL_NAME,
        temperature=0.2,
    )
