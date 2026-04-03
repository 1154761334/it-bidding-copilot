"""
CrewAI 任务链定义与 Crew 编排
串联 4 个 Agent 完成 RFP 拆解 → 商务响应 → 技术方案 的完整编标流程
"""
import json
from typing import Optional

from crewai import Task, Crew, Process

from agents.bid_analyst import create_bid_analyst
from agents.commercial_specialist import create_commercial_specialist
from agents.technical_architect import create_technical_architect


# ============================================================
# 任务定义
# ============================================================

def create_rfp_analysis_task(agent, rfp_text: str) -> Task:
    """
    任务 1: RFP 拆解分析
    由拆标专家从招标文件中提取结构化需求
    """
    return Task(
        description=f"""请全面分析以下招标文件内容，动态提取所有关键投标要素。

你必须输出以下结构化内容（JSON 格式）：

1. **项目概况**：项目名称、预算金额、服务期限、投标截止时间
2. **商务资质要求**：逐条列出所有商务门槛（资质证书、业绩要求、财务条件等），标注是否为强制项
3. **技术/服务参数**：逐条列出所有技术指标和服务要求，按分类归组
4. **废标条款**：提取所有一票否决项，不得遗漏
5. **评分标准**：按大类列出权重和各评分子项分值

重要原则：
- 严格根据原文提取，不得编造
- 废标条款必须100%完整
- 参数指标必须保留原文的精确数值

招标文件内容：
{rfp_text[:6000]}
""",
        expected_output="""JSON 格式的结构化 RFP 分析结果，包含：
- project_info: 项目基本信息
- commercial_requirements: 商务资质要求列表
- technical_requirements: 技术参数要求列表
- veto_clauses: 废标条款列表
- scoring_criteria: 评分标准表""",
        agent=agent,
    )


def create_cross_validation_task(agent, rfp_text: str) -> Task:
    """
    任务 2: 交叉核实
    同一个拆标专家对提取结果进行二次比对验证
    """
    return Task(
        description=f"""请对上一步的 RFP 提取结果进行严格的二次交叉核实。

核实方法：
1. 将每一条提取结果与原文内容逐一比对
2. 检查是否有遗漏的关键要求（特别是废标条款）
3. 检查提取的数值、期限、分值是否与原文完全一致
4. 检查强制项/非强制项的标注是否准确

对每一类提取结果输出核实结论：
- ✅ 正确：与原文一致
- ❌ 有误：标注错误内容并给出修正
- ⚠️ 遗漏：补充遗漏的条目

原文参考：
{rfp_text[:6000]}
""",
        expected_output="""交叉核实报告，包含：
- 各类提取结果的核实状态
- 发现的错误及修正
- 补充的遗漏项
- 最终确认的完整提取结果""",
        agent=agent,
    )


def create_commercial_response_task(agent, rfp_requirements: str, enterprise_info: str) -> Task:
    """
    任务 3: 商务响应编写
    商务合规管家根据 RFP 要求和企业资料编写商务响应
    """
    return Task(
        description=f"""请根据以下 RFP 商务要求和企业资料，编写完整的《商务响应表》。

编写要求：
1. 逐条回应 RFP 中的每一项商务资质要求
2. 对于企业已具备的资质，标注证书名称和有效期
3. 对于缺失或不确定的材料，标注 [需人工确认补充]
4. 编写业绩案例响应，选取最匹配的历史项目
5. 汇总财务状况说明

绝对禁止：捏造任何资质信息或业绩数据

RFP 商务要求：
{rfp_requirements}

企业资料：
{enterprise_info}
""",
        expected_output="""完整的商务响应内容，包含：
- 企业资质响应（逐条对照）
- 业绩案例响应（含项目详情）
- 财务状况说明
- 缺失材料清单（标注[需人工确认补充]）""",
        agent=agent,
    )


def create_technical_response_task(agent, rfp_requirements: str, knowledge_context: str) -> Task:
    """
    任务 4: 技术方案编写
    首席技术主笔根据 RFP 要求撰写技术与服务响应方案
    """
    return Task(
        description=f"""请根据以下 RFP 技术要求和知识库参考资料，撰写高质量的《技术与服务响应方案》。

编写总纲：
1. 整体方案设计 — 架构理念、核心优势、差异化竞争力
2. 基础设施详细方案 — 逐条响应 RFP 技术参数，提供具体数值
3. SLA 服务保障方案 — 列出可量化的 SLA 承诺表，附赔偿条款
4. 安全合规方案 — 等保合规、物理安全、网络安全、数据安全
5. 运维团队方案 — 团队配置、资质要求、排班制度
6. 应急预案 — 分级响应、灾备方案、RPO/RTO 承诺

写作风格要求：
- 干练专业，拒绝套话空话
- 每个指标响应必须有具体数值
- SLA 承诺必须附赔偿条款才有说服力
- 方案必须可落地执行

RFP 技术要求：
{rfp_requirements}

知识库参考：
{knowledge_context}
""",
        expected_output="""完整的技术方案文档，包含6个章节：
1. 整体方案设计
2. 基础设施详细方案
3. SLA 服务保障方案（含 SLA 指标承诺表）
4. 安全合规方案
5. 运维团队方案（含人员配置表）
6. 应急预案（含分级响应表和灾备方案）""",
        agent=agent,
    )


# ============================================================
# Crew 编排
# ============================================================

class BiddingCrew:
    """投标编标 Crew — 编排多 Agent 协作完成编标任务"""

    def __init__(self, llm=None, tools: dict = None, verbose: bool = True):
        """
        Args:
            llm: LangChain LLM 实例（所有 Agent 共用）
            tools: 工具字典 {"analyst": [...], "commercial": [...], "technical": [...]}
            verbose: 是否打印日志
        """
        self.llm = llm
        self.verbose = verbose

        tool_map = tools or {}
        self.analyst = create_bid_analyst(llm, tool_map.get("analyst"), verbose)
        self.commercial = create_commercial_specialist(llm, tool_map.get("commercial"), verbose)
        self.architect = create_technical_architect(llm, tool_map.get("technical"), verbose)

    def run_rfp_analysis(self, rfp_text: str) -> dict:
        """
        Phase A: RFP 拆解 + 交叉核实
        返回结构化的 RFP 分析结果
        """
        task_analyze = create_rfp_analysis_task(self.analyst, rfp_text)
        task_validate = create_cross_validation_task(self.analyst, rfp_text)

        crew = Crew(
            agents=[self.analyst],
            tasks=[task_analyze, task_validate],
            process=Process.sequential,
            verbose=self.verbose,
        )

        result = crew.kickoff()
        return {"raw_output": str(result), "status": "completed"}

    def run_bid_writing(
        self,
        rfp_requirements: str,
        enterprise_info: str,
        knowledge_context: str = "",
    ) -> dict:
        """
        Phase B: 商务响应 + 技术方案编写
        返回编标结果
        """
        task_commercial = create_commercial_response_task(
            self.commercial, rfp_requirements, enterprise_info
        )
        task_technical = create_technical_response_task(
            self.architect, rfp_requirements, knowledge_context
        )

        crew = Crew(
            agents=[self.commercial, self.architect],
            tasks=[task_commercial, task_technical],
            process=Process.sequential,
            verbose=self.verbose,
        )

        result = crew.kickoff()
        return {
            "raw_output": str(result),
            "status": "completed",
            "tasks": {
                "commercial": str(task_commercial.output) if task_commercial.output else "",
                "technical": str(task_technical.output) if task_technical.output else "",
            },
        }

    def run_full_pipeline(
        self,
        rfp_text: str,
        enterprise_info: str,
        knowledge_context: str = "",
    ) -> dict:
        """
        全流程编标：RFP 拆解 → 交叉核实 → 商务响应 → 技术方案
        """
        # Phase A
        analysis = self.run_rfp_analysis(rfp_text)

        # Phase B
        writing = self.run_bid_writing(
            rfp_requirements=analysis["raw_output"],
            enterprise_info=enterprise_info,
            knowledge_context=knowledge_context,
        )

        return {
            "analysis": analysis,
            "writing": writing,
            "status": "completed",
        }
