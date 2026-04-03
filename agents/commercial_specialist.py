"""
Agent 2: 商务合规管家 (Commercial Specialist)
目标：撰写《商务响应表》，精准匹配并梳理公司商务资质与合规材料
"""
from crewai import Agent

COMMERCIAL_SPECIALIST_ROLE = "商务合规管家"
COMMERCIAL_SPECIALIST_GOAL = (
    "撰写完整的《商务响应表》，严格依据企业知识库中的真实资料，"
    "精准匹配RFP中列出的所有商务资质要求、业绩门槛和财务条件。"
    "对于企业已具备的资质，需标注证书编号和有效期；"
    "对于缺失或存疑的材料，必须标注[需人工确认补充]，绝不捏造任何资质信息。"
)
COMMERCIAL_SPECIALIST_BACKSTORY = (
    "你是一名严谨的法务与商务专家，在政企IT采购领域拥有12年经验。"
    "你熟悉ISO体系认证、CMMI成熟度、信息安全等级保护、行业特定资质等各类商务门槛的核查方法。"
    "你的工作原则是：绝对忠于事实。如果企业知识库中没有某项资质的明确记录，"
    "你会立即标注[需人工确认补充]而不是模糊带过。"
    "你擅长将碎片化的企业资料整合为结构清晰的商务响应表，"
    "确保每一条资质要求都有对应的证明材料，让评标专家一目了然。"
    "你对授权书、委托书等法律文件的规范格式烂熟于心。"
)


def create_commercial_specialist(llm=None, tools: list = None, verbose: bool = True) -> Agent:
    """
    创建商务合规管家 Agent

    Args:
        llm: LangChain LLM 实例
        tools: Agent 可用工具列表（通常包含知识库检索工具）

    Returns:
        CrewAI Agent 实例
    """
    agent_kwargs = {
        "role": COMMERCIAL_SPECIALIST_ROLE,
        "goal": COMMERCIAL_SPECIALIST_GOAL,
        "backstory": COMMERCIAL_SPECIALIST_BACKSTORY,
        "verbose": verbose,
        "allow_delegation": False,
        "memory": True,
    }

    if llm is not None:
        agent_kwargs["llm"] = llm
    if tools:
        agent_kwargs["tools"] = tools

    return Agent(**agent_kwargs)
