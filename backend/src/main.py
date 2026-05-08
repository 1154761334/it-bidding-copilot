"""
IT Bidding Copilot API - Main Entrypoint
Serves: REST API, LobeChat Plugin endpoints, and the LangGraph workflow.
"""
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import json

from .config import repo_path, settings
from .database import engine, Base, get_db
from . import models
from .parser import parse_to_markdown
from .workflow import bid_workflow, BidState
from .llm import llm_chat
from .api_workbench import (
    approve_plan,
    artifact_response,
    attach_source_file,
    create_project_record,
    generate_execution,
    generate_plan,
    generate_review,
    get_project_record,
    list_project_artifacts,
    list_project_records,
    project_detail,
    public_project,
    run_demo_real_case,
    search_evidence_payload,
)

from langchain_core.messages import HumanMessage

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="IT Bidding Copilot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory project state store (will be replaced by DB persistence later)
# ---------------------------------------------------------------------------
project_states: dict[int, dict] = {}
_next_id = 1


# ---------------------------------------------------------------------------
# Core API Endpoints
# ---------------------------------------------------------------------------
@app.get("/")
def read_root():
    return {
        "message": "IT Bidding Copilot API v1.0",
        "llm_provider": "openai_compatible",
        "llm_model": settings.LLM_MODEL,
    }


@app.post("/parse/")
async def parse_document(file: UploadFile = File(...)):
    """Parse an uploaded file (PDF/DOCX/XLSX/PPTX) to Markdown."""
    contents = await file.read()
    markdown_content = parse_to_markdown(contents, file.filename)
    return {"filename": file.filename, "markdown": markdown_content}


# ---------------------------------------------------------------------------
# Workflow API Endpoints
# ---------------------------------------------------------------------------
class StartProjectRequest(BaseModel):
    project_name: str
    tender_markdown: Optional[str] = None


class UploadAndStartRequest(BaseModel):
    project_name: str


class CreateProjectRequest(BaseModel):
    name: str
    bidder: str = ""
    project_role: str = ""


@app.get("/health")
def health(db: Session = Depends(get_db)):
    """Health endpoint consumed by the /bid workbench."""
    evidence_count = db.query(models.EvidenceItem).count()
    return {
        "status": "ok",
        "version": "1.0.0",
        "data_dir": str(repo_path(settings.BIDDING_DATA_DIR).resolve()),
        "core_available": True,
        "evidence_store_available": True,
        "evidence_count": evidence_count,
        "project_count": len(list_project_records()),
        "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
    }


@app.post("/projects")
def create_project(req: CreateProjectRequest):
    project = create_project_record(req.name, req.bidder, req.project_role)
    return {"project_id": project["id"], "project": public_project(project)}


@app.get("/projects")
def projects():
    return {"projects": [public_project(project) for project in list_project_records()]}


@app.get("/projects/{project_id}")
def project(project_id: str):
    return project_detail(get_project_record(project_id))


@app.post("/projects/{project_id}/files")
async def upload_project_file(project_id: str, purpose: str, file: UploadFile = File(...)):
    contents = await file.read()
    markdown = ""
    try:
        markdown = parse_to_markdown(contents, file.filename or "uploaded")
    except Exception:
        if file.filename and file.filename.lower().endswith((".md", ".txt")):
            markdown = contents.decode("utf-8", errors="replace")
        else:
            raise
    record = attach_source_file(project_id, file.filename or "uploaded", contents, purpose, markdown)
    return {"project_id": project_id, "file": record}


@app.post("/projects/{project_id}/plan")
def plan_project(project_id: str, db: Session = Depends(get_db)):
    return generate_plan(project_id, db)


@app.post("/projects/{project_id}/approve-plan")
def approve_project_plan(project_id: str):
    return approve_plan(project_id)


@app.post("/projects/{project_id}/execute")
def execute_project(project_id: str, db: Session = Depends(get_db)):
    return generate_execution(project_id, db)


@app.post("/projects/{project_id}/review")
def review_project(project_id: str, db: Session = Depends(get_db)):
    return generate_review(project_id, db)


@app.get("/projects/{project_id}/artifacts")
def project_artifacts(project_id: str):
    return {"project_id": project_id, "artifacts": list_project_artifacts(project_id)}


@app.get("/projects/{project_id}/artifacts/{artifact_name}")
def project_artifact(project_id: str, artifact_name: str):
    return artifact_response(project_id, artifact_name)


@app.get("/evidence/search")
def evidence_search(query: str, category: Optional[str] = None, top_k: int = 10, db: Session = Depends(get_db)):
    return search_evidence_payload(db, query=query, category=category, top_k=top_k)


@app.post("/demo/real-case")
def demo_real_case(db: Session = Depends(get_db)):
    return run_demo_real_case(db)


@app.post("/api/project/start")
async def start_project(req: StartProjectRequest):
    """Start a new bidding project with the tender document content."""
    global _next_id
    pid = _next_id
    _next_id += 1

    if not req.tender_markdown:
        raise HTTPException(status_code=400, detail="tender_markdown is required")

    # Run the analyze step of the workflow
    initial_state: BidState = {
        "project_id": pid,
        "messages": [HumanMessage(content=f"开始分析项目: {req.project_name}")],
        "parsed_markdown": req.tender_markdown,
        "plan_report": "",
        "missing_materials": [],
        "scoring_items": [],
        "hard_requirements": [],
        "drafts": {},
        "review_report": "",
        "current_mode": "plan",
    }

    # Run only until the human_confirmation breakpoint
    final_state = None
    for output in bid_workflow.stream(initial_state):
        for node_name, state_update in output.items():
            if final_state is None:
                final_state = {**initial_state, **state_update}
            else:
                final_state.update(state_update)
            if state_update.get("current_mode") == "plan_confirmation_needed":
                # Stop here - wait for user confirmation
                project_states[pid] = final_state
                return {
                    "project_id": pid,
                    "status": "plan_generated",
                    "plan_report": final_state.get("plan_report", ""),
                    "missing_materials": final_state.get("missing_materials", []),
                    "scoring_items": final_state.get("scoring_items", []),
                    "hard_requirements": final_state.get("hard_requirements", []),
                    "message": "计划已生成，请确认后继续起草。",
                }

    # Should not reach here in normal flow
    project_states[pid] = final_state or initial_state
    return {"project_id": pid, "status": "unknown", "message": "Workflow completed unexpectedly."}


@app.post("/api/project/{project_id}/confirm")
async def confirm_project(project_id: int):
    """User confirms the plan. Triggers Execute Mode -> Review Mode."""
    if project_id not in project_states:
        raise HTTPException(status_code=404, detail="Project not found")

    state = project_states[project_id]

    # Continue the workflow from human_confirmation through draft and review
    state["current_mode"] = "executing"
    state["messages"] = state.get("messages", []) + [HumanMessage(content="用户已确认计划，开始起草。")]

    # Re-run the remaining workflow steps manually
    # Step 1: Draft
    from .workflow import draft_sections_node, review_node
    draft_result = draft_sections_node(state)
    state.update(draft_result)

    # Step 2: Review
    review_result = review_node(state)
    state.update(review_result)

    project_states[project_id] = state

    return {
        "project_id": project_id,
        "status": "completed",
        "drafts": {name: content[:500] + "..." if len(content) > 500 else content
                   for name, content in state.get("drafts", {}).items()},
        "review_report": state.get("review_report", ""),
        "message": f"起草和质检完成。共生成 {len(state.get('drafts', {}))} 个章节。",
    }


@app.get("/api/project/{project_id}/drafts")
async def get_project_drafts(project_id: int):
    """Get all generated drafts for a project."""
    if project_id not in project_states:
        raise HTTPException(status_code=404, detail="Project not found")
    state = project_states[project_id]
    return {
        "project_id": project_id,
        "drafts": state.get("drafts", {}),
        "review_report": state.get("review_report", ""),
    }


@app.get("/api/project/{project_id}/draft/{section_name}")
async def get_draft_section(project_id: int, section_name: str):
    """Get a specific draft section."""
    if project_id not in project_states:
        raise HTTPException(status_code=404, detail="Project not found")
    state = project_states[project_id]
    drafts = state.get("drafts", {})
    if section_name not in drafts:
        raise HTTPException(status_code=404, detail=f"Section '{section_name}' not found")
    return {"section_name": section_name, "content": drafts[section_name]}


# ---------------------------------------------------------------------------
# Chat endpoint (conversational interface)
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    message: str
    project_id: Optional[int] = None


@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    """Simple chat endpoint that uses LLM to answer bidding-related questions."""
    system = "你是一位专业的投标助手。帮助用户解答关于投标文件、评分标准、材料准备等问题。回答要简洁专业。"

    context = ""
    if req.project_id and req.project_id in project_states:
        state = project_states[req.project_id]
        context = f"\n\n当前项目的招标文件摘要：\n{state.get('plan_report', '')[:2000]}"

    response = llm_chat(
        system_prompt=system,
        user_prompt=req.message + context,
        temperature=0.5,
    )
    return {"reply": response}


# ---------------------------------------------------------------------------
# LobeChat Plugin Manifest
# ---------------------------------------------------------------------------
@app.get("/plugin/manifest.json")
def get_plugin_manifest():
    return {
        "api": [
            {
                "url": "http://localhost:8000/plugin/analyze",
                "name": "analyze_tender",
                "description": "分析招标文件，提取评分项、资格条件、缺失材料。",
                "parameters": {
                    "properties": {
                        "project_name": {"type": "string", "description": "项目名称"},
                        "tender_content": {"type": "string", "description": "招标文件内容（Markdown格式）"},
                    },
                    "type": "object",
                    "required": ["project_name", "tender_content"],
                },
            },
            {
                "url": "http://localhost:8000/plugin/draft",
                "name": "generate_drafts",
                "description": "确认计划后执行起草，生成各章节草稿和质检报告。",
                "parameters": {
                    "properties": {"project_id": {"type": "integer"}},
                    "type": "object",
                    "required": ["project_id"],
                },
            },
        ],
        "identifier": "bidding-copilot",
        "meta": {
            "avatar": "📝",
            "tags": ["bidding", "投标"],
            "title": "投标起草引擎",
            "description": "智能投标文档分析与起草工作台。",
        },
        "version": "1",
    }


class PluginAnalyzeRequest(BaseModel):
    project_name: str
    tender_content: str


@app.post("/plugin/analyze")
async def plugin_analyze(req: PluginAnalyzeRequest):
    """LobeChat plugin: analyze tender document."""
    start_req = StartProjectRequest(
        project_name=req.project_name,
        tender_markdown=req.tender_content,
    )
    return await start_project(start_req)


class PluginDraftRequest(BaseModel):
    project_id: int


@app.post("/plugin/draft")
async def plugin_draft(req: PluginDraftRequest):
    """LobeChat plugin: confirm plan and generate drafts."""
    return await confirm_project(req.project_id)
