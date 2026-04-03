"""
Embedding 模型配置
"""
from typing import Optional
from config import OPENAI_API_KEY, OPENAI_BASE_URL, EMBEDDING_MODEL


def get_embeddings(model_name: str = None):
    """
    获取 Embedding 模型实例

    Returns:
        LangChain Embeddings 实例，如果依赖不可用则返回 None
    """
    model = model_name or EMBEDDING_MODEL

    if not OPENAI_API_KEY:
        return None

    try:
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(
            model=model,
            openai_api_key=OPENAI_API_KEY,
            openai_api_base=OPENAI_BASE_URL,
        )
    except ImportError:
        return None
