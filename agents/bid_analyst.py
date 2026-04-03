"""
Agent 1: 需求统筹与拆标专家 (Bid Analyst)
目标：全面拆解招标文件，动态提取核心采购需求、商务门槛、废标条款及评分标准
"""
from crewai import Agent

BID_ANALYST_ROLE = "需求统筹与拆标专家"
BID_ANALYST_GOAL = (
    "全面拆解招标文件，动态提取核心采购需求（无论是SLA、参数指标、合规证明还是资质门槛），"
    "识别商务门槛与一票否决的废标条款，提炼评分标准与权重分布，"
    "确保后续编标环节零遗漏、零误读。"
)
BID_ANALYST_BACKSTORY = (
    "你是一名拥有15年IT综合项目（含基建、云、数据中心、信息化系统）售前咨询与统筹经验的资深专家。"
    "你曾主导参与过超过200个政企IT招投标项目，对合同条款、潜在雷区和评标规则极其敏感。"
    "你的核心能力是从复杂的招标文件中精准提取关键信息，并以结构化方式呈现，"
    "让编标团队能够一目了然地理解甲方的真实需求与评分侧重点。"
    "你尤其擅长识别隐藏在长篇条款中的废标风险和加分项，"
    "并会反复比对原文以确保提取结果的准确性。"
)


def create_bid_analyst(llm=None, tools: list = None, verbose: bool = True) -> Agent:
    """
    创建拆标专家 Agent

    Args:
        llm: LangChain LLM 实例
        tools: Agent 可用工具列表
        verbose: 是否打印详细日志

    Returns:
        CrewAI Agent 实例
    """
    agent_kwargs = {
        "role": BID_ANALYST_ROLE,
        "goal": BID_ANALYST_GOAL,
        "backstory": BID_ANALYST_BACKSTORY,
        "verbose": verbose,
        "allow_delegation": False,
        "memory": True,
    }

    if llm is not None:
        agent_kwargs["llm"] = llm
    if tools:
        agent_kwargs["tools"] = tools

    return Agent(**agent_kwargs)
