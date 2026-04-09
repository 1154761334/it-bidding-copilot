import anyio
from typing import List, Dict
from sqlalchemy import text, and_
from sqlalchemy.orm import Session

from api.models.assets_v2 import EnterpriseCase, EnterpriseCertificate, AssetChunk
from api.core.config import get_settings
from utils.query_rewriter import StructuredQuery
from utils.embedding_engine import EmbeddingEngine

class HybridRetriever:
    """
    企业级双路检索引擎：
    1. SQL 硬过滤：拦截不满足金额、期限、等级要求的资产
    2. Vector 软匹配：在合规资产中寻找业务最契合的案例
    """
    def __init__(self, db: Session, embedder=None):
        self.db = db
        self.embedder = embedder or EmbeddingEngine()
        self.embedding_disabled_reason: str | None = None

    async def search_cases(self, query: StructuredQuery, company_id: int = None, limit: int = 3) -> List[EnterpriseCase]:
        """
        针对历史案例的混合检索 (带重排序)
        """
        filters = []
        if company_id:
            filters.append(EnterpriseCase.company_id == company_id)
        if query.min_amount:
            filters.append(EnterpriseCase.contract_amount >= query.min_amount)
        if query.earliest_date:
            filters.append(EnterpriseCase.sign_date >= query.earliest_date)
        if query.target_category:
            filters.append(EnterpriseCase.compliance_keywords.contains(query.target_category))
            
        # 1. 召回更多候选集 (例如 10 个)
        # 将 CPU 密集型的向量生成放入线程池
        query_vector = await anyio.to_thread.run_sync(self._get_embedding, query.semantic_context)
        
        # DB 查询 (同步调用)
        candidates = self.db.query(EnterpriseCase).filter(and_(*filters)).order_by(
            EnterpriseCase.embedding.l2_distance(query_vector)
        ).limit(limit * 3).all()
        
        if not candidates:
            return []

        # 2. 第二阶段重排序 (Cross-Encoder)
        docs = [c.description or "" for c in candidates]
        # 将 CPU 密集型的重排序放入线程池
        scores = await anyio.to_thread.run_sync(self.embedder.rerank, query.semantic_context, docs)
        
        # 配对、排序并取前 limit
        scored_candidates = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
        return [c for c, s in scored_candidates[:limit]]

    async def search_certificates(self, requirement: str, company_id: int) -> List[EnterpriseCertificate]:
        """
        根据标书要求检索资质 (如: "CMMI", "ISO")
        """
        query_vector = await anyio.to_thread.run_sync(self._get_embedding, requirement)
        results = self.db.query(EnterpriseCertificate).filter(
            EnterpriseCertificate.company_id == company_id
        ).order_by(
            EnterpriseCertificate.embedding.l2_distance(query_vector)
        ).limit(2).all()
        return results

    async def search_chunks(self, query_text: str, company_id: int, limit: int = 5) -> List[AssetChunk]:
        """
        原子级区块检索 (带重排序)
        """
        query_vector = await anyio.to_thread.run_sync(self._get_embedding, query_text)
        # 1. 召回更多候选集
        candidates = self.db.query(AssetChunk).filter(
            AssetChunk.company_id == company_id
        ).order_by(
            AssetChunk.embedding.l2_distance(query_vector)
        ).limit(limit * 3).all()
        
        if not candidates:
            return []

        # 2. 第二阶段重排序
        docs = [c.content or "" for c in candidates]
        scores = await anyio.to_thread.run_sync(self.embedder.rerank, query_text, docs)
        
        scored_candidates = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
        return [c for c, s in scored_candidates[:limit]]

    def _get_embedding(self, text: str) -> List[float]:
        """
        同步辅助方法：获取文本向量 (由 anyio.to_thread 驱动)
        """
        try:
            if self.embedder is None:
                return [0.0] * 1024
            return self.embedder.embed_query(text)
        except Exception as e:
            message = str(e)
            if self.embedding_disabled_reason is None:
                self.embedding_disabled_reason = message
                print(f"❌ [Embedding Error] {message}")
            return [0.0] * 1024

    def compliance_check(self, requirement: str) -> Dict:
        """
        一键式合规性检查逻辑
        """
        # 逻辑略...
        pass
