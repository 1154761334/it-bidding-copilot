"""
LangGraph 循环审标状态机
实现 review → decide → revise 的循环工作流，最多 3 轮
"""
import json
import operator
from typing import Annotated, TypedDict, Literal, Optional

from langgraph.graph import StateGraph, END

from agents.chief_reviewer import create_chief_reviewer, REVIEW_OUTPUT_FORMAT
from config import MAX_REVIEW_ROUNDS


# ============================================================
# 状态定义
# ============================================================

class ReviewState(TypedDict):
    """审标工作流状态"""
    # 投标文件内容（各章节）
    bid_content: str
    # RFP 废标条款列表
    veto_clauses: list[str]
    # RFP 评分标准
    scoring_criteria: str
    # 审查意见历史
    review_history: Annotated[list[dict], operator.add]
    # 当前轮次
    revision_count: int
    # 是否通过
    is_approved: bool
    # 最终审查报告
    final_report: str
    # LLM 实例引用（传递用）
    llm: Optional[object]


# ============================================================
# 节点函数
# ============================================================

def review_node(state: ReviewState) -> dict:
    """
    审查节点 — 红脸评标组长审查投标文件
    """
    llm = state.get("llm")
    bid_content = state["bid_content"]
    veto_clauses = state.get("veto_clauses", [])
    scoring_criteria = state.get("scoring_criteria", "")
    revision_count = state["revision_count"]

    review_prompt = f"""你是一名极其苛刻的独立外部评委（红脸评标组长），请对以下投标文件进行第 {revision_count + 1} 轮严格审查。

## 审查依据

### 废标条款（一票否决项）
{json.dumps(veto_clauses, ensure_ascii=False, indent=2) if veto_clauses else "（未提供废标条款）"}

### 评分标准
{scoring_criteria if scoring_criteria else "（未提供评分标准）"}

## 审查要求
1. 逐条检查废标条款是否全部规避
2. 逐条检查技术参数是否已响应
3. 检查 SLA 承诺是否合理且有赔偿条款
4. 检查商务资质是否齐全
5. 检查是否有遗漏的关键响应项

{REVIEW_OUTPUT_FORMAT}

## 投标文件内容
{bid_content[:8000]}
"""

    if llm:
        response = llm.invoke(review_prompt)
        review_text = response.content
    else:
        # Mock 审查结果
        if revision_count == 0:
            review_text = _mock_review_round_1()
        else:
            review_text = _mock_review_round_2()

    # 解析审查结果判断是否通过
    has_veto_risk = "废标风险" in review_text and "不通过" in review_text
    is_approved = not has_veto_risk

    review_record = {
        "round": revision_count + 1,
        "review_text": review_text,
        "is_approved": is_approved,
        "has_veto_risk": has_veto_risk,
    }

    return {
        "review_history": [review_record],
        "is_approved": is_approved,
        "final_report": review_text,
    }


def revise_node(state: ReviewState) -> dict:
    """
    修改节点 — 根据审查意见修改投标文件
    """
    llm = state.get("llm")
    bid_content = state["bid_content"]
    latest_review = state["review_history"][-1] if state["review_history"] else {}
    review_text = latest_review.get("review_text", "")
    revision_count = state["revision_count"]

    revise_prompt = f"""请根据以下审查意见，对投标文件进行修改。

## 修改要求
1. 针对"废标风险"标注的问题，必须全部修复
2. 针对"扣分风险"标注的问题，尽量修复
3. 针对"优化建议"，在不影响已有正确内容的前提下优化
4. 保持修改后文档的整体连贯性

## 审查意见（第 {revision_count + 1} 轮）
{review_text}

## 当前投标文件
{bid_content[:8000]}

请输出修改后的完整投标文件内容。
"""

    if llm:
        response = llm.invoke(revise_prompt)
        revised_content = response.content
    else:
        # Mock 修改
        revised_content = bid_content + f"\n\n--- 第 {revision_count + 1} 轮整改内容 ---\n（已根据审查意见修改）"

    return {
        "bid_content": revised_content,
        "revision_count": revision_count + 1,
    }


# ============================================================
# 条件路由
# ============================================================

def should_continue(state: ReviewState) -> Literal["revise", "accept"]:
    """
    判断是否继续循环：
    - 通过 → accept（终态）
    - 未通过且轮次 < MAX → revise（修改后重审）
    - 未通过但轮次 >= MAX → accept（强制终止）
    """
    if state["is_approved"]:
        return "accept"
    if state["revision_count"] >= MAX_REVIEW_ROUNDS:
        return "accept"  # 超过最大轮次，强制结束
    return "revise"


# ============================================================
# 构建 Graph
# ============================================================

def build_review_graph() -> StateGraph:
    """
    构建 LangGraph 循环审标状态机

    工作流：
        review → decide → revise → review → ... → accept

    Returns:
        编译后的 StateGraph 实例
    """
    graph = StateGraph(ReviewState)

    # 添加节点
    graph.add_node("review", review_node)
    graph.add_node("revise", revise_node)

    # 设置入口
    graph.set_entry_point("review")

    # 条件边：review → decide → revise 或 accept
    graph.add_conditional_edges(
        "review",
        should_continue,
        {
            "revise": "revise",
            "accept": END,
        },
    )

    # revise → review（循环）
    graph.add_edge("revise", "review")

    return graph.compile()


def run_review_workflow(
    bid_content: str,
    veto_clauses: list[str] = None,
    scoring_criteria: str = "",
    llm=None,
) -> dict:
    """
    执行完整的循环审标工作流

    Args:
        bid_content: 投标文件全文
        veto_clauses: 废标条款列表
        scoring_criteria: 评分标准文本
        llm: LLM 实例

    Returns:
        {
            "is_approved": bool,
            "total_rounds": int,
            "review_history": list[dict],
            "final_report": str,
            "final_content": str,
        }
    """
    graph = build_review_graph()

    initial_state: ReviewState = {
        "bid_content": bid_content,
        "veto_clauses": veto_clauses or [],
        "scoring_criteria": scoring_criteria,
        "review_history": [],
        "revision_count": 0,
        "is_approved": False,
        "final_report": "",
        "llm": llm,
    }

    # 执行状态机
    final_state = graph.invoke(initial_state)

    return {
        "is_approved": final_state["is_approved"],
        "total_rounds": final_state["revision_count"],
        "review_history": final_state["review_history"],
        "final_report": final_state["final_report"],
        "final_content": final_state["bid_content"],
    }


# ============================================================
# Mock 审查结果（Phase 2 兼容）
# ============================================================

def _mock_review_round_1() -> str:
    return """## 审查结论
- 总体判定：不通过
- 废标风险项数：2
- 扣分风险项数：2
- 优化建议项数：1

## 废标风险 (⛔ 必须修改)
1. [商务响应] 投标保证金(50万元)在商务响应中未提及缴纳方式和时间，可能导致废标 → 补充保证金缴纳方式（银行转账/保函）和截止时间
2. [技术方案] SLA承诺表中部分指标未与招标要求逐条对应 → 逐条核对RFP技术参数并补全响应

## 扣分风险 (⚠️ 强烈建议修改)
1. [技术方案] "整体方案设计"章节缺少差异化竞争优势分析，可能影响15分中的得分 → 补充与竞品对比的差异化优势
2. [商务响应] 等保三级测评报告有效期标注[需人工确认]，评标时可能被质疑 → 明确标注有效期限

## 优化建议 (ℹ️ 建议优化)
1. [技术方案] 应急预案分级表可增加实际案例说明 → 补充1-2个真实处置案例"""


def _mock_review_round_2() -> str:
    return """## 审查结论
- 总体判定：有条件通过
- 废标风险项数：0
- 扣分风险项数：1
- 优化建议项数：0

## 废标风险 (⛔ 必须修改)
（无）

## 扣分风险 (⚠️ 强烈建议修改)
1. [商务响应] 等保三级测评报告有效期仍需人工确认 → 建议在投标前完成确认

## 优化建议 (ℹ️ 建议优化)
（无）"""
