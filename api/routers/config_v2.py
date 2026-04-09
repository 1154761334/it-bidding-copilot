from typing import Optional

import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.core.config import get_settings
from api.services.model_runtime_service import get_model_runtime_info

router = APIRouter()


class ConfigUpdate(BaseModel):
    llm_model: str
    api_key: Optional[str] = None
    base_url: str
    embedding_model: Optional[str] = None


@router.get("/")
async def get_settings_config():
    current = get_settings()
    return {
        "LLM_MODEL": current.resolved_llm_model,
        "LLM_API_KEY": "********" if current.resolved_llm_api_key else "",
        "LLM_BASE_URL": current.resolved_llm_base_url,
        "EMBEDDING_MODEL": current.EMBEDDING_MODEL,
        "DATABASE_URL": current.DATABASE_URL,
    }


@router.get("/capabilities")
async def get_model_capabilities():
    return get_model_runtime_info()


@router.post("/update")
async def update_settings(config: ConfigUpdate):
    try:
        env_path = ".env"
        existing_env = {}
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    if "=" in line:
                        key, value = line.strip().split("=", 1)
                        existing_env[key] = value

        existing_env["LLM_MODEL"] = config.llm_model
        if config.api_key is not None:
            existing_env["LLM_API_KEY"] = config.api_key
        existing_env["LLM_BASE_URL"] = config.base_url
        if config.embedding_model is not None:
            existing_env["EMBEDDING_MODEL"] = config.embedding_model

        with open(env_path, "w", encoding="utf-8") as f:
            for key, value in existing_env.items():
                f.write(f"{key}={value}\n")

        os.environ["LLM_MODEL"] = config.llm_model
        if config.api_key is not None:
            os.environ["LLM_API_KEY"] = config.api_key
        os.environ["LLM_BASE_URL"] = config.base_url
        if config.embedding_model is not None:
            os.environ["EMBEDDING_MODEL"] = config.embedding_model

        return {"status": "success", "message": "Configuration persisted successfully"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/test-connection")
async def test_connection():
    try:
        from langchain_openai import ChatOpenAI
        from langchain_openai import OpenAIEmbeddings

        current = get_settings()
        if not current.resolved_llm_api_key.strip():
            return {"status": "error", "message": "API Key is empty. Please enter a real key to test."}

        llm = ChatOpenAI(
            openai_api_key=current.resolved_llm_api_key,
            openai_api_base=current.resolved_llm_base_url,
            model=current.resolved_llm_model,
            max_retries=1,
            timeout=10,
        )
        llm.invoke("ping")
        if current.EMBEDDING_MODEL.strip():
            embedder = OpenAIEmbeddings(
                model=current.EMBEDDING_MODEL.strip(),
                openai_api_key=current.resolved_llm_api_key,
                openai_api_base=current.resolved_llm_base_url,
            )
            vector = embedder.embed_query("ping")
            return {
                "status": "success",
                "message": f"Connectivity verified. Chat and embedding are responsive. embedding_dim={len(vector)}",
            }
        return {"status": "success", "message": "Connectivity verified. Chat is responsive. Embedding model not configured."}
    except Exception as exc:
        return {"status": "error", "message": f"Connection failed: {str(exc)}"}
