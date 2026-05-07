"""
Evidence retrieval engine using pgvector for semantic search.
Provides RAG capabilities for the bidding workflow.
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from openai import OpenAI
from .models import EvidenceItem
from .config import settings

_embed_client: OpenAI | None = None


def _get_embed_client() -> OpenAI:
    """Create the embedding client lazily so missing API keys do not break keyword smoke tests."""
    global _embed_client
    if not settings.EMBEDDING_API_KEY:
        raise RuntimeError("EMBEDDING_API_KEY is not configured")
    if _embed_client is None:
        _embed_client = OpenAI(
            api_key=settings.EMBEDDING_API_KEY,
            base_url=settings.EMBEDDING_BASE_URL,
        )
    return _embed_client


def get_embedding(text: str) -> list[float]:
    """Get an embedding vector for a text string."""
    text = text[:8000]  # Truncate to avoid token limits
    response = _get_embed_client().embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=text,
    )
    return response.data[0].embedding


def keyword_search_evidence(
    db: Session,
    query: str,
    category: str = None,
    sub_type: str = None,
    top_k: int = 10,
) -> list[EvidenceItem]:
    """
    Perform a keyword-based search using PostgreSQL Full Text Search (or simple ILIKE).
    This is used as a fallback if embeddings are unavailable.
    """
    keywords = [k.strip() for k in query.replace("，", " ").replace(",", " ").split() if len(k.strip()) > 1]
    if not keywords:
        keywords = [query]

    q = db.query(EvidenceItem)

    clauses = []
    for kw in keywords[:5]: # limit to first 5 keywords
        clauses.append(
            or_(EvidenceItem.title.ilike(f"%{kw}%"), EvidenceItem.text_content.ilike(f"%{kw}%"))
        )
        clauses.append(EvidenceItem.tags.contains([kw]))

    if clauses:
        q = q.filter(or_(*clauses))

    if category:
        q = q.filter(EvidenceItem.category == category)
    if sub_type:
        q = q.filter(EvidenceItem.sub_type == sub_type)

    return q.limit(top_k).all()


def search_evidence(
    db: Session,
    query: str,
    category: str = None,
    sub_type: str = None,
    top_k: int = 5,
) -> list[EvidenceItem]:
    """
    Semantic search over the evidence store with keyword fallback.
    """
    if settings.EMBEDDING_API_KEY:
        try:
            query_embedding = get_embedding(query)

            q = db.query(EvidenceItem)

            filters = []
            if category:
                filters.append(EvidenceItem.category == category)
            if sub_type:
                filters.append(EvidenceItem.sub_type == sub_type)

            if filters:
                q = q.filter(and_(*filters))

            q = q.filter(EvidenceItem.embedding.isnot(None))
            q = q.order_by(EvidenceItem.embedding.cosine_distance(query_embedding))

            results = q.limit(top_k).all()
            if results:
                return results
        except Exception as e:
            print(f"Warning: Semantic search failed, falling back to keyword search: {e}")

    # Fallback to keyword search
    return keyword_search_evidence(db, query, category, sub_type, top_k)


def search_evidence_by_tags(
    db: Session,
    tags: list[str],
    category: str = None,
    top_k: int = 10,
) -> list[EvidenceItem]:
    """Search evidence by matching tags (exact match)."""
    q = db.query(EvidenceItem)

    if category:
        q = q.filter(EvidenceItem.category == category)

    for tag in tags:
        q = q.filter(EvidenceItem.tags.contains([tag]))

    return q.limit(top_k).all()


def format_evidence_for_llm(items: list[EvidenceItem]) -> str:
    """Format retrieved evidence items into a context string for the LLM."""
    if not items:
        return "【未找到相关佐证材料】"

    parts = []
    for i, item in enumerate(items, 1):
        part = f"--- 佐证材料 {i} ---\n"
        part += f"证据ID: EVID-{item.id}\n"
        part += f"类型: {item.category}/{item.sub_type}\n"
        part += f"标题: {item.title}\n"
        if item.source_page:
            part += f"原文页码: {item.source_page}\n"
        if item.image_paths:
            part += f"关联图片: {', '.join(str(p) for p in item.image_paths[:3])}\n"
        content = item.text_content or ""
        if len(content) > 1000:
            content = content[:1000] + "...[截断]"
        part += f"内容:\n{content}\n"
        parts.append(part)

    return "\n".join(parts)
