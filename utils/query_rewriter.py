from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import date
import json
import re
import instructor

class StructuredQuery(BaseModel):
    """消歧后的结构化查询对象"""
    target_category: str = Field(..., description="资质类别 (QUALIFICATION), 技术要求 (TECHNICAL), 或基本信息 (GENERAL)")
    min_amount: Optional[float] = Field(None, description="最低合同金额要求 (单位: 元)")
    must_have_level: Optional[str] = Field(None, description="必须具备的等级 (如: 三级, 五级)")
    earliest_date: Optional[date] = Field(None, description="最早允许的签署日期/颁发日期")
    semantic_context: str = Field(..., description="用于向量检索的详细语义描述")

class QueryRewriter:
    """
    意图消歧引擎：由于招标文件语言模糊，需要将其转化为精确的操作语义
    """
    def __init__(self, llm):
        # 如果传入的是 LLMClient，自动获取 raw_client
        raw_client = getattr(llm, "raw_client", llm)
        # 使用 instructor 包装 LLM 客户端
        self.client = instructor.from_openai(raw_client)

    def rewrite_requirement(self, raw_requirement: str) -> StructuredQuery:
        """
        利用 instructor 将非结构化要求拆解为精确的结构化查询对象
        """
        try:
            return self.client.chat.completions.create(
                model="gpt-4o",
                response_model=StructuredQuery,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一名资深招投标数字化专家。请将非结构化要求转换为严谨的结构化查询对象。"
                    },
                    {
                        "role": "user",
                        "content": f"要求原文：\"{raw_requirement}\"\n\n请根据原文提取结构化信息。如果提到日期，请根据当前日期计算出具体日期。"
                    }
                ]
            )
        except Exception as e:
            print(f"Instructor rewrite failed: {e}")
            return self._fallback_rewrite(raw_requirement)

    def _fallback_rewrite(self, raw_requirement: str) -> StructuredQuery:
        lowered = raw_requirement.lower()
        target_category = "GENERAL"
        if any(keyword in raw_requirement for keyword in ["资质", "证书", "认证", "营业执照", "社保"]):
            target_category = "QUALIFICATION"
        elif any(keyword in raw_requirement for keyword in ["案例", "云平台", "技术", "兼容", "性能", "服务"]):
            target_category = "TECHNICAL"

        amount_match = re.search(r"(\d+(?:\.\d+)?)\s*(万|万元|元)", raw_requirement)
        min_amount = None
        if amount_match:
            value = float(amount_match.group(1))
            unit = amount_match.group(2)
            min_amount = value * 10000 if "万" in unit else value

        must_have_level = None
        level_match = re.search(r"([一二三四五12345])[级等]", raw_requirement)
        if level_match:
            must_have_level = f"{level_match.group(1)}级"

        semantic_context = re.sub(r"\s+", " ", raw_requirement).strip() or lowered
        return StructuredQuery(
            target_category=target_category,
            min_amount=min_amount,
            must_have_level=must_have_level,
            earliest_date=None,
            semantic_context=semantic_context,
        )
