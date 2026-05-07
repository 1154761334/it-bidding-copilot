"""
LLM client module.
Uses the OpenAI-compatible API from Volcengine to call Kimi-k2.6.
"""
from openai import OpenAI
from .config import settings

client = OpenAI(api_key=settings.LLM_API_KEY or "missing", base_url=settings.LLM_BASE_URL)

def llm_chat(system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
    """Send a chat completion request and return the assistant's reply."""
    if not settings.LLM_API_KEY:
        raise RuntimeError("LLM_API_KEY is not configured")

    print(f"  [LLM] Calling {settings.LLM_MODEL}...")
    try:
        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
        )
        content = response.choices[0].message.content
        print(f"  [LLM] Success ({len(content)} chars)")
        return content
    except Exception as e:
        print(f"  [LLM] Error: {e}")
        raise
