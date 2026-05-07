"""
LangGraph workflow for the bidding copilot.
Orchestrates: Plan Mode -> Human Confirmation -> Execute Mode -> Review Mode.
Uses Kimi-k2.6 via Volcengine for all LLM calls.
"""
from typing import TypedDict, Annotated, Sequence
import operator
import json
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from .llm import llm_chat
from .database import SessionLocal
from .models import BidProject
from .evidence import search_evidence, format_evidence_for_llm


# ---------------------------------------------------------------------------
# State definition
# ---------------------------------------------------------------------------
class BidState(TypedDict):
    project_id: int
    messages: Annotated[Sequence[BaseMessage], operator.add]
    parsed_markdown: str
    plan_report: str          # structured plan output
    missing_materials: list[str]
    scoring_items: list[str]
    hard_requirements: list[str]
    drafts: dict[str, str]    # section_name -> markdown content
    review_report: str        # QA review output
    current_mode: str         # plan, plan_confirmation_needed, executing, execute_complete, reviewing, done


# ---------------------------------------------------------------------------
# Node 1: Analyze Tender (Plan Mode)
# ---------------------------------------------------------------------------
PLAN_SYSTEM_PROMPT = """你是一位资深投标专家。用户会给你一份招标文件的全文（Markdown格式）。
请你严格按照以下JSON格式输出分析结果，不要输出任何其他内容：

```json
{
  "项目名称": "...",
  "采购预算": "...",
  "投标截止时间": "...",
  "采购内容摘要": "一句话概括",
  "资格条件": ["▲1. ...", "▲2. ..."],
  "实质性条款": ["..."],
  "重要技术指标": ["△1. ...", "△2. ..."],
  "评分办法": [
    {"评分项": "...", "分值": "...", "得分规则": "..."}
  ],
  "需要准备的材料清单": ["...", "..."],
  "当前缺失材料": ["...", "..."],
  "建议投标文件目录": ["第一章 ...", "第二章 ..."],
  "起草策略建议": "..."
}
```"""

def analyze_tender_node(state: BidState) -> dict:
    """Plan Mode: Analyze the tender document using LLM."""
    print("\n=== [NODE: analyze_tender] ===")
    doc = state.get("parsed_markdown", "")

    raw_response = llm_chat(
        system_prompt=PLAN_SYSTEM_PROMPT,
        user_prompt=f"请分析以下招标文件：\n\n{doc}",
        temperature=0.2,
    )
    print(f"LLM plan response length: {len(raw_response)} chars")

    # Try to extract structured data from the LLM response
    missing = []
    hard_reqs = []
    scoring = []
    try:
        # Strip markdown code fences if present
        cleaned = raw_response
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0]
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0]
        parsed = json.loads(cleaned.strip())
        missing = parsed.get("当前缺失材料", [])
        hard_reqs = parsed.get("实质性条款", []) or parsed.get("资格条件", [])
        scoring_raw = parsed.get("评分办法", [])
        scoring = [f"{s.get('评分项','')}: {s.get('分值','')}" for s in scoring_raw if isinstance(s, dict)]
    except Exception as e:
        print(f"Warning: Could not parse LLM JSON: {e}")

    # Persist analysis to database
    db = SessionLocal()
    try:
        project = db.query(BidProject).filter(BidProject.id == state["project_id"]).first()
        if not project:
            project = BidProject(id=state["project_id"], name="New Project")
            db.add(project)
        
        project.requirements = hard_reqs
        project.scoring_items = scoring
        # project.plan_report = raw_response # If we add this column
        db.commit()
        print(f"  [DB] Saved analysis for project {state['project_id']}")
    except Exception as e:
        print(f"  [DB] Error saving analysis: {e}")
    finally:
        db.close()

    return {
        "messages": [AIMessage(content=raw_response)],
        "plan_report": raw_response,
        "missing_materials": missing,
        "hard_requirements": hard_reqs,
        "scoring_items": scoring,
        "current_mode": "plan_confirmation_needed",
    }


# ---------------------------------------------------------------------------
# Node 2: Human Confirmation (Breakpoint)
# ---------------------------------------------------------------------------
def human_confirmation_node(state: BidState) -> dict:
    """Pause point: in production this is an interrupt; in tests it passes through."""
    print("\n=== [NODE: human_confirmation] ===")
    print("Workflow paused. User must confirm the plan before drafting begins.")
    return {
        "messages": [HumanMessage(content="用户已确认计划，开始起草。")],
        "current_mode": "executing",
    }


# ---------------------------------------------------------------------------
# Node 3: Draft Sections (Execute Mode)
# ---------------------------------------------------------------------------
DRAFT_SYSTEM_PROMPT = """你是一位资深投标文档撰写专家。
用户会给你：
1. 招标文件原文
2. 章节名称和撰写要求
3. 【可选】真实佐证材料（来自公司素材库，包含证书、合同、截图等）

你的任务：
根据招标要求撰写投标响应内容。
**重要规则**：
- 如果提供了【真实佐证材料】，请优先引用这些材料中的真实信息（如证书编号、公司名称、项目金额等）。
- 在响应偏离表时，如果找到了对应的证书或截图，请在"投标响应"或"说明"中明确标注"详见附件：[标题]"。
- 内容要专业、详实，紧扣招标要求。
- 输出格式为 Markdown。"""

SECTIONS_TO_DRAFT = [
    ("商务偏离表", "请根据招标文件中的▲实质性条款，生成商务偏离表。格式为 Markdown 表格，列包括：序号、招标文件条款号、招标要求、投标响应、偏离说明。"),
    ("技术偏离表", "请根据招标文件中的△重要技术指标和一般技术要求，生成技术偏离表。格式为 Markdown 表格，列包括：序号、招标文件条款号、技术要求、投标响应、偏离说明。"),
    ("技术方案", "请根据招标文件的采购需求和技术指标，撰写一份完整的私有云建设技术方案，包括：整体架构设计、计算虚拟化方案、分布式存储方案、安全隔离方案。"),
    ("售后服务方案", "请根据招标文件要求，撰写售后服务方案，包括：服务响应时间承诺、驻场服务安排、培训计划、质保期安排。"),
]

def draft_sections_node(state: BidState) -> dict:
    """Execute Mode: Draft each section using LLM with RAG support."""
    print("\n=== [NODE: draft_sections] ===")
    doc = state.get("parsed_markdown", "")
    drafts = {}

    db = SessionLocal()
    try:
        for section_name, instruction in SECTIONS_TO_DRAFT:
            print(f"  Drafting: {section_name}...")
            
            # RAG: Search for relevant evidence based on section name and doc keywords
            # We use a broad search for the section to get context
            evidence_items = search_evidence(db, query=f"{section_name} {doc[:500]}", top_k=8)
            evidence_context = format_evidence_for_llm(evidence_items)
            
            prompt = f"招标文件原文：\n{doc}\n\n【真实佐证材料】：\n{evidence_context}\n\n撰写指令：\n{instruction}"
            
            draft_md = llm_chat(
                system_prompt=DRAFT_SYSTEM_PROMPT,
                user_prompt=prompt,
                temperature=0.4,
            )
            drafts[section_name] = draft_md
            print(f"  Done: {section_name} ({len(draft_md)} chars)")
    finally:
        db.close()

    # Persist drafts to database
    db = SessionLocal()
    try:
        project = db.query(BidProject).filter(BidProject.id == state["project_id"]).first()
        if project:
            # Update existing drafts or create new dictionary
            current_drafts = dict(project.parsed_documents or {})
            current_drafts.update(drafts)
            project.parsed_documents = current_drafts
            db.commit()
            print(f"  [DB] Saved {len(drafts)} drafts to project {state['project_id']}")
    except Exception as e:
        print(f"  [DB] Error saving drafts: {e}")
    finally:
        db.close()

    return {
        "drafts": drafts,
        "current_mode": "execute_complete",
        "messages": [AIMessage(content=f"起草完成。共生成 {len(drafts)} 个章节草稿，已接入公司真实素材库。")],
    }


# ---------------------------------------------------------------------------
# Node 4: Review (QA Mode)
# ---------------------------------------------------------------------------
REVIEW_SYSTEM_PROMPT = """你是一位投标质检专家。
用户会给你招标文件原文和投标文件的各章节草稿。
请你逐项检查：
1. ▲实质性条款是否全部响应？是否有遗漏？
2. △重要技术指标是否全部覆盖？有无负偏离？
3. 评分项是否都有对应内容？
4. 项目名称、预算金额、日期等关键信息是否一致？
5. 是否有缺失的证明材料？

请按以下格式输出质检报告：
🔴 高风险：...
🟠 中风险：...
🟡 一般问题：...
🟢 已覆盖：...
📊 总体评估：..."""

def review_node(state: BidState) -> dict:
    """Review Mode: Run QA checks against the drafts."""
    print("\n=== [NODE: review] ===")
    doc = state.get("parsed_markdown", "")
    drafts = state.get("drafts", {})

    drafts_text = ""
    for name, content in drafts.items():
        drafts_text += f"\n\n--- 章节：{name} ---\n{content}"

    review = llm_chat(
        system_prompt=REVIEW_SYSTEM_PROMPT,
        user_prompt=f"招标文件原文：\n{doc}\n\n投标草稿内容：\n{drafts_text}",
        temperature=0.2,
    )
    print(f"Review report generated ({len(review)} chars)")

    return {
        "review_report": review,
        "current_mode": "done",
        "messages": [AIMessage(content=review)],
    }


# ---------------------------------------------------------------------------
# Routing logic
# ---------------------------------------------------------------------------
def route_next_step(state: BidState):
    mode = state.get("current_mode")
    if mode == "plan_confirmation_needed":
        return "human_confirmation"
    elif mode == "execute_complete":
        return "review"
    return END


# ---------------------------------------------------------------------------
# Build the graph
# ---------------------------------------------------------------------------
workflow = StateGraph(BidState)

workflow.add_node("analyze", analyze_tender_node)
workflow.add_node("human_confirmation", human_confirmation_node)
workflow.add_node("draft_sections", draft_sections_node)
workflow.add_node("review", review_node)

workflow.add_edge(START, "analyze")
workflow.add_conditional_edges("analyze", route_next_step)
workflow.add_edge("human_confirmation", "draft_sections")
workflow.add_edge("draft_sections", "review")
workflow.add_edge("review", END)

bid_workflow = workflow.compile()
