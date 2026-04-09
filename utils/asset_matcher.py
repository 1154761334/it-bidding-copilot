from typing import List, Dict
from sqlalchemy.orm import Session
from api.models.rfp_v2 import RFPRequirement
from utils.hybrid_retriever import HybridRetriever
from utils.query_rewriter import StructuredQuery

class AssetMatcher:
    """
    资产自动对标引擎：
    自动根据标书需求搜索最匹配的资产，并预估得分/风险。
    """
    def __init__(self, db: Session):
        self.db = db
        self.retriever = HybridRetriever(db)

    def match_requirement(self, requirement: RFPRequirement, company_id: int):
        """
        执行单个需求的自动对标
        """
        query_text = requirement.description
        
        # 1. 构造搜索上下文
        sq = StructuredQuery(
            semantic_context=query_text,
            target_category=requirement.category
        )
        
        # 2. 根据类型搜索不同库
        if requirement.category == "QUALIFICATION":
            # 搜索证书库
            results = self.retriever.search_certificates(query_text, company_id)
            if results:
                requirement.match_status = "PASS"
                requirement.match_comment = f"已匹配到匹配度最高的证书: {results[0].raw_name}"
            else:
                requirement.match_status = "FAIL"
                requirement.match_comment = "⚠️ 资产库中未找到完全匹配的资质。预计失分或存废标风险。"
                
        elif requirement.category == "TECHNICAL":
            # 搜索案例库
            results = self.retriever.search_cases(sq, company_id=company_id)
            if results:
                requirement.match_status = "PARTIAL"
                requirement.match_comment = f"找到 {len(results)} 个相似案例，建议进一步核对金额。最高分 15 分，当前预计可得 {min(len(results)*3, 15)} 分。"
            else:
                requirement.match_status = "FAIL"
                requirement.match_comment = "未找到同类案例。"

        return requirement
