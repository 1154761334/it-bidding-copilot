from typing import Any

from api.core.config import get_settings


def get_model_runtime_info() -> dict[str, Any]:
    settings = get_settings()
    api_key = settings.resolved_llm_api_key
    base_url = settings.resolved_llm_base_url
    llm_model = settings.resolved_llm_model
    embedding_model = settings.EMBEDDING_MODEL.strip()

    compatibility_notes: list[str] = []
    if "ark.cn-beijing.volces.com/api/coding/v3" in base_url and llm_model.lower() == "auto":
        compatibility_notes.append(
            "Ark Coding Auto may reject some structured ChatOpenAI calls; deterministic fallbacks remain enabled."
        )
    if not embedding_model:
        compatibility_notes.append("Embedding is disabled; vector retrieval falls back to zero vectors.")

    return {
        "provider": settings.LLM_PROVIDER,
        "api_key_configured": bool(api_key),
        "base_url": base_url,
        "llm_model": llm_model,
        "embedding_model": embedding_model or None,
        "chat_enabled": bool(api_key and llm_model),
        "embedding_enabled": bool(api_key and embedding_model),
        "fallbacks": {
            "structured_extraction": True,
            "query_rewrite": True,
            "draft_generation": True,
            "embedding_zero_vector": not bool(embedding_model),
        },
        "compatibility_notes": compatibility_notes,
    }


def build_parser_trace(*, strategy: str, parse_result: dict[str, Any] | None = None) -> dict[str, Any]:
    parse_result = parse_result or {}
    return {
        "strategy": strategy,
        "markdown_length": len(parse_result.get("markdown", "")),
        "images_count": len(parse_result.get("images", [])),
        "coordinates_count": len(parse_result.get("coordinates", [])),
    }
