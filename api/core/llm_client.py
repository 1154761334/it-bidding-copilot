from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from api.core.config import get_settings

class LLMClient:
    """
    统一 LLM 调用适配层：
    支持更换模型提供商，并封装了针对“投标场景”的常用 Prompt 结构。
    """
    def __init__(self, role: str = "ANALYSIS", streaming: bool = False, callbacks: list = None, **kwargs):
        current_settings = get_settings()
        role_override = getattr(current_settings, f"LLM_MODEL_{role.upper()}", "")

        self.provider = current_settings.LLM_PROVIDER
        self.api_key = current_settings.resolved_llm_api_key
        self.base_url = current_settings.resolved_llm_base_url
        self.model = role_override or current_settings.resolved_llm_model

        # 初始化 LangChain 客户端
        self.llm = ChatOpenAI(
            model=self.model,
            openai_api_key=self.api_key,
            openai_api_base=self.base_url,
            streaming=streaming,
            callbacks=callbacks,
            **kwargs
        )
        
        # [NEW] 初始化原始 OpenAI 客户端，供 instructor 等库使用
        from openai import OpenAI
        self.raw_client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        print(f"[LLMClient] role={role} model={self.model} base_url={self.base_url}")

    @staticmethod
    def is_configured() -> bool:
        current_settings = get_settings()
        return bool(current_settings.resolved_llm_api_key and current_settings.resolved_llm_model)

    def analyze_scoring_logic(self, table_text: str) -> str:
        """针对复杂评分表进行结构化解析 (同步)"""
        prompt = ChatPromptTemplate.from_template("""
        你是一个资深的招投标专家。请分析以下招标文件中的评分表文本，
        将其转换为 JSON 格式，包含: item (评价项), criteria (评分细则), max_score (分值)。
        
        表格文本:
        {table_text}
        
        输出要求:
        只输出 JSON 数组，不要任何解释。
        """)
        chain = prompt | self.llm
        return chain.invoke({"table_text": table_text}).content

    async def analyze_scoring_logic_async(self, table_text: str) -> str:
        """针对复杂评分表进行结构化解析 (异步)"""
        prompt = ChatPromptTemplate.from_template("""
        你是一个资深的招投标专家。请分析以下招标文件中的评分表文本，
        将其转换为 JSON 格式，包含: item (评价项), criteria (评分细则), max_score (分值)。
        
        表格文本:
        {table_text}
        
        输出要求:
        只输出 JSON 数组，不要任何解释。
        """)
        chain = prompt | self.llm
        res = await chain.ainvoke({"table_text": table_text})
        return res.content

    def synthesize_bid_content(self, scoring_point: str, criteria: str, internal_assets: str) -> str:
        """对撞生成技术方案内容 (同步)"""
        prompt = ChatPromptTemplate.from_template("""
        你是一个私有云技术方案专家。
        【任务】请针对以下“得分点”编写响应方案，必须命中“评分标准”。
        【得分项】: {scoring_point}
        【评分标准】: {criteria}
        【我方已有方案/案例】: {internal_assets}
        
        【要求】:
        1. 格式专业，使用工业级术语。
        2. 结构清晰，必须包含具体的响应动作（如何满足该标准）。
        3. 字数不少于 800 字。
        """)
        chain = prompt | self.llm
        return chain.invoke({
            "scoring_point": scoring_point,
            "criteria": criteria,
            "internal_assets": internal_assets
        }).content

    async def synthesize_bid_content_async(self, scoring_point: str, criteria: str, internal_assets: str) -> str:
        """对撞生成技术方案内容 (异步)"""
        prompt = ChatPromptTemplate.from_template("""
        你是一个私有云技术方案专家。
        【任务】请针对以下“得分点”编写响应方案，必须命中“评分标准”。
        【得分项】: {scoring_point}
        【评分标准】: {criteria}
        【我方已有方案/案例】: {internal_assets}
        
        【要求】:
        1. 格式专业，使用工业级术语。
        2. 结构清晰，必须包含具体的响应动作（如何满足该标准）。
        3. 字数不少于 800 字。
        """)
        chain = prompt | self.llm
        res = await chain.ainvoke({
            "scoring_point": scoring_point,
            "criteria": criteria,
            "internal_assets": internal_assets
        })
        return res.content
